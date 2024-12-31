from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from pytube import YouTube
from django.conf import settings
import os
import assemblyai as aai
import openai
from .models import BlogPost

# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def generateBlog(request):
     if request.method == 'POST':
          try:
               data = json.loads(request.body)
               yt_link = data['link']
               
          except(KeyError, json.JSONDecodeError):
               return JsonResponse({'error': 'Invalid data'}, status=400)
     
          #youtube video title
          title = yt_title(yt_link)

          #get transcrypt  
          transcription = get_transcription(yt_link)
          if not transcription:
               return JsonResponse({'error': 'Failed to generate transcript'}, status=500)
          #Use chatgpt to generate the article
          blog_content = generate_article_transcript(transcription)
          if not blog_content:
               return JsonResponse({'error': 'Failed to generate blog from transcript'}, status=500)
          
          #save article to db
          new_article = BlogPost.objects.create(
               user= request.user,
               youtube_link = title,
               youtube_title = yt_link,
               generated_content = blog_content, 
          )
          new_article.save()
          #return article as a response
          return JsonResponse({'content': blog_content})
     else:
          return JsonResponse({'error': 'Invalid request method'}, status=405)          

     

def yt_title(link):
     yt = YouTube(link)
     title = yt.title
     return title

def download_audio(link):
     yt = YouTube(link)
     video = yt.streams.filter(only_audio=True).first()
     out_file = video.download(output_path=settings.MEDIA_ROOT)
     base, ext = os.path.splitext(out_file)
     new_file = base + '.mp3'
     os.rename(out_file, new_file)
     return new_file

def get_transcription(link):
     audio_file = download_audio(link)
     aai.settings.api_key = ""

     transcriber = aai.Transcriber()
     transcript = transcriber.transcribe(audio_file)

     return transcript.text

def generate_article_transcript(transcription):
     openai.api_key = ""
     prompt = f"Based on the following transcript from a youtube video, 
     write a comprehensive blog article based on the transcript, edit any parts that make it sound like a youtube video for it to look like an organic blog article:\n\{transcription}\n\nArticle: "
     response = openai.Completion.create(
          model="text-davinci-003",
          prompt = prompt
          max_tokens=1000
     )

     generated_content = response.choices[0].text.strip()
     return generated_content


def blog_list(request):
     blog_articles = BlogPost.objects.filter(user=request.user)
     return render(request, 'articles.html', {'blog_articles': blog_articles})

def blog_details(request, pk):
     blog_article_details = BlogPost.objects.get(id=pk)
     if request.user == blog_article_details.user:
          return render(request, 'article-details.html', {'blog_article_details': blog_article_details})
     else:
          return redirect('/')

def user_signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
             error_message = "Invlid username or password combination"
             return render(request, 'signin.html', {'error_message':error_message})
    return render(request, 'signin.html')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']

        if password == repeatPassword:
                try:
                     user = User.objects.create_user(username, email, password)
                     user.save()
                     login(request, user)
                     return redirect('/')
                except:
                     error_message = 'Error creating account'
                     return render(request, 'signup.html' ,{'error_message':error_message})

        else:
            error_message = 'Password does not match'
            return render(request, 'signup.html' ,{'error_message':error_message})
    
    return render(request, 'sigup.html')

def user_logout(request):
    logout(request)
    return redirect('/')


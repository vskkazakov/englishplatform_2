from django.shortcuts import render

def index(request):
    return render(request, 'mainApp/main.html')
def contact(request):
    return render(request, 'mainApp/contact.html', {'values' : ['Если вопросы', '1234567']})

from django.shortcuts import render

def index(request):
    return render(request, 'mainApp/index.html')
def contact(request):
    return render(request, 'mainApp/contact.html', {'values' : ['Если вопросы', '1234567']})

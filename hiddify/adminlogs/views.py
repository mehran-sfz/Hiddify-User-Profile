from adminlogs.action import add_admin_log
from adminlogs.models import Message
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect


def SendMessageToAll(request):
    
    if request.method == 'POST':
            
        title = request.POST.get('title', None)
        content = request.POST.get('content', None)
        
        if not title or not content:
            messages.error(request, 'لطفا همه ی فیلد ها را پر کنید!')
            return redirect('/admin-panel/messages')
        
        try:
            Message.objects.create(title=title, content=content)
            messages.success(request, 'با موفقیت ارسال شد')
        except Exception as e:
            add_admin_log(action=f'Error in sending message to all: {str(e)}', category='admin', user=request.user)
            messages.error(request, 'ارور در ارسال پیام:', str(e))
            return redirect('/admin-panel/messages')
        
    return redirect('/admin-panel/messages')
        
def DeactiveMessage(request, pk):

    instance = get_object_or_404(Message, pk=pk)
    
    if instance:
        if instance.status == True:
            instance.status = False
        else:
            instance.status = True
        instance.save()
        messages.success(request, 'با موفقیت تغییر یافت')
             
    
    return redirect('/admin-panel/messages')

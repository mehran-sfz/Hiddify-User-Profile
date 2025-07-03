from django.shortcuts import redirect
from django.contrib import messages
from adminlogs.models import Message
from adminlogs.action import add_admin_log
from django.shortcuts import get_object_or_404


def SendMessageToAll(request):
    
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/home/')
    
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
    
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/home/')
    
    instance = get_object_or_404(Message, pk=pk)
    
    if instance:
        if instance.status == True:
            instance.status = False
        else:
            instance.status = True
        instance.save()
        messages.success(request, 'با موفقیت تغییر یافت')
             
    
    return redirect('/admin-panel/messages')

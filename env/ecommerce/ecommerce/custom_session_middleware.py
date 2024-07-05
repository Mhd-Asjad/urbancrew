from django.contrib.sessions.middleware import SessionMiddleware

class CustomSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        if 'admin' in request.path :
            request.session_key = 'admin_' + (request.session.session_key or '')
        else:
            request.session_key = 'user_' + (request.session.session_key or '')
        super(CustomSessionMiddleware, self).process_request(request)
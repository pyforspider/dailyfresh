from django.contrib.auth.decorators import login_required


class LoginRequiredMixin:
	@classmethod
	def as_view(cls, **kwargs):
		view = super(LoginRequiredMixin, cls).as_view(**kwargs)
		return login_required(view)

# -*- coding: utf-8 -*-
import datetime
from cms.utils import get_language_from_request
from django.contrib.auth.models import User
from django.core.urlresolvers import resolve
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, DetailView

from .models import Post, BlogCategory
from .settings import BLOG_PAGINATION, BLOG_POSTS_LIST_TRUNCWORDS_COUNT


class BaseBlogView(object):

    def get_queryset(self):
        language = get_language_from_request(self.request)
        manager = self.model._default_manager.language(language)
        if not self.request.user.is_staff:
            manager = manager.filter(publish=True)
        return manager

    def render_to_response(self, context, **response_kwargs):
        response_kwargs['current_app'] = resolve(self.request.path).namespace
        return super(BaseBlogView, self).render_to_response(context, **response_kwargs)


class PostListView(BaseBlogView, ListView):
    model = Post
    context_object_name = 'post_list'
    template_name = "djangocms_blog/post_list.html"
    paginate_by = BLOG_PAGINATION

    def get_context_data(self, **kwargs):
        context = super(PostListView, self).get_context_data(**kwargs)
        context['TRUNCWORDS_COUNT'] = BLOG_POSTS_LIST_TRUNCWORDS_COUNT
        return context

class PostDetailView(BaseBlogView, DetailView):
    model = Post
    context_object_name = 'post'
    template_name = "djangocms_blog/post_detail.html"
    slug_field = 'translations__slug'


class PostArchiveView(BaseBlogView, ListView):
    model = Post
    context_object_name = 'post_list'
    template_name = "djangocms_blog/post_list.html"
    date_field = 'date_published'
    allow_empty = True
    allow_future = True
    paginate_by = BLOG_PAGINATION

    def get_queryset(self):
        qs = super(PostArchiveView, self).get_queryset()
        if 'month' in self.kwargs:
            qs = qs.filter(**{"%s__month" % self.date_field: self.kwargs['month']})
        if 'year' in self.kwargs:
            qs = qs.filter(**{"%s__year" % self.date_field: self.kwargs['year']})
        return qs

    def get_context_data(self, **kwargs):
        kwargs['month'] = int(self.kwargs.get('month')) if 'month' in self.kwargs else None
        kwargs['year'] = int(self.kwargs.get('year')) if 'year' in self.kwargs else None
        if kwargs['year']:
            kwargs['archive_date'] = datetime.date(kwargs['year'], kwargs['month'] or 1, 1)
        return super(PostArchiveView, self).get_context_data(**kwargs)


class TaggedListView(BaseBlogView, ListView):
    model = Post
    context_object_name = 'post_list'
    template_name = "djangocms_blog/post_list.html"
    paginate_by = BLOG_PAGINATION

    def get_queryset(self):
        qs = super(TaggedListView, self).get_queryset()
        return qs.filter(tags__slug=self.kwargs['tag'])

    def get_context_data(self, **kwargs):
        kwargs['tagged_entries'] = (self.kwargs.get('tag')
                                    if 'tag' in self.kwargs else None)
        return super(TaggedListView, self).get_context_data(**kwargs)


class AuthorEntriesView(BaseBlogView, ListView):
    model = Post
    context_object_name = 'post_list'
    template_name = "djangocms_blog/post_list.html"
    paginate_by = BLOG_PAGINATION

    def get_queryset(self):
        qs = super(AuthorEntriesView, self).get_queryset()
        if 'username' in self.kwargs:
            qs = qs.filter(author__username=self.kwargs['username'])
        return qs

    def get_context_data(self, **kwargs):
        kwargs['author'] = User.objects.get(username=self.kwargs.get('username'))
        return super(AuthorEntriesView, self).get_context_data(**kwargs)


class CategoryEntriesView(BaseBlogView, ListView):
    model = Post
    context_object_name = 'post_list'
    template_name = "djangocms_blog/post_list.html"
    _category = None
    paginate_by = BLOG_PAGINATION

    @property
    def category(self):
        if not self._category:
            language = get_language_from_request(self.request)
            self._category = BlogCategory._default_manager.language(language).get(
                translations__language_code=language,
                translations__slug=self.kwargs['category'])
        return self._category

    def get_queryset(self):
        qs = super(CategoryEntriesView, self).get_queryset()
        if 'category' in self.kwargs:
            qs = qs.filter(categories=self.category.pk)
        return qs

    def get_context_data(self, **kwargs):
        kwargs['category'] = self.category
        return super(CategoryEntriesView, self).get_context_data(**kwargs)

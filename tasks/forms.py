from django import forms
from tasks.models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "xp_reward"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 w-full transition-all",
                    "placeholder": "O que precisa ser feito?",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 w-full h-16 resize-none transition-all",
                    "placeholder": "Detalhes da tarefa (opcional)...",
                    "rows": 2,
                }
            ),
            "xp_reward": forms.NumberInput(
                attrs={
                    "class": "bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 w-24 text-center transition-all",
                    "min": 1,
                    "max": 100,
                }
            ),
        }

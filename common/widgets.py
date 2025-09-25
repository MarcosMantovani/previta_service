from django import forms


class WhatsAppEditorWidget(forms.TextInput):
    template_name = 'common/whatsapp_editor.html'

    class Media:
        css = {
            'all': ('https://use.fontawesome.com/releases/v5.6.3/css/all.css', 'common/css/whatsapp-editor.css',)
        }
        js = (
            'admin/js/vendor/jquery/jquery.js',
            'admin/js/jquery.init.js', 
            'common/js/whatsapp-editor.js',
        )


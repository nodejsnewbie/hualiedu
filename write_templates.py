from pathlib import Path

def write_template(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

# change_list.html
change_list_content = '''{% extends "admin/change_list.html" %}
{% load i18n admin_urls static admin_list %}

{% block object-tools-items %}
    <li>
        <a href="{% url 'admin:grading_repository_add' %}" class="addlink">
            {% blocktranslate with cl.opts.verbose_name as name %}Add {{ name }}{% endblocktranslate %}
        </a>
    </li>
{% endblock %}

{% block content %}
    <div id="content-main">
        {% if action_form and actions_on_top and cl.show_admin_actions %}
            {% admin_actions %}
        {% endif %}
        {% result_list cl %}
        {% if action_form and actions_on_bottom and cl.show_admin_actions %}
            {% admin_actions %}
        {% endif %}
    </div>
{% endblock %}

{% block extrahead %}
    {{ block.super }}
    <style>
        .field-get_sync_status {
            font-weight: bold;
        }
        .field-get_sync_status.synced {
            color: #28a745;
        }
        .field-get_sync_status.not_synced {
            color: #dc3545;
        }
        .action-buttons {
            display: flex;
            gap: 8px;
        }
    </style>
{% endblock %}'''

write_template('templates/admin/grading/repository/change_list.html', change_list_content)

# change_form.html
change_form_content = '''{% extends "admin/change_form.html" %}
{% load i18n admin_urls static admin_modify %}

{% block object-tools-items %}
    <li>
        <a href="{% url 'admin:grading_repository_changelist' %}" class="viewlink">
            {% translate "View on site" %}
        </a>
    </li>
    {% if has_absolute_url %}
        <li>
            <a href="{{ absolute_url }}" class="viewlink">
                {% translate "View on site" %}
            </a>
        </li>
    {% endif %}
    {% if has_delete_permission %}
        <li>
            <a href="{% url 'admin:grading_repository_delete' original.pk|admin_urlquote %}" class="deletelink">
                {% translate "Delete" %}
            </a>
        </li>
    {% endif %}
{% endblock %}

{% block content %}
    <div id="content-main">
        <form {% if has_file_field %}enctype="multipart/form-data" {% endif %}action="{{ form_url }}" method="post" id="{{ opts.model_name }}_form" novalidate>
            {% csrf_token %}
            {% block form_top %}{% endblock %}
            {% if errors %}
                <p class="errornote">
                    {% if errors|length == 1 %}
                        {% translate "Please correct the error below." %}
                    {% else %}
                        {% translate "Please correct the errors below." %}
                    {% endif %}
                </p>
                {{ adminform.form.non_field_errors }}
            {% endif %}
            {% for fieldset in adminform %}
                {% include "admin/includes/fieldset.html" %}
            {% endfor %}
            {% block after_field_sets %}{% endblock %}
            {% for inline_admin_formset in inline_admin_formsets %}
                {% include inline_admin_formset.opts.template %}
            {% endfor %}
            {% block after_related_objects %}{% endblock %}
            {% block submit_buttons_bottom %}{% submit_row %}{% endblock %}
            {% block prepopulated_fields_js %}
                {{ block.super }}
            {% endblock %}
            {% block extra_js %}{% endblock %}
        </form>
    </div>
{% endblock %}

{% block extrahead %}
    {{ block.super }}
    <style>
        .field-url {
            width: 100%;
        }
        .field-url input {
            width: 100%;
        }
        .help {
            color: #666;
            font-size: 12px;
            margin-top: 5px;
            display: block;
        }
    </style>
{% endblock %}'''

write_template('templates/admin/grading/repository/change_form.html', change_form_content)

# change_branch.html
change_branch_content = '''{% extends "admin/base_site.html" %}
{% load i18n admin_urls static admin_modify %}

{% block extrastyle %}
    {{ block.super }}
    <link rel="stylesheet" type="text/css" href="{% static "admin/css/forms.css" %}">
{% endblock %}

{% block coltype %}colM{% endblock %}

{% block bodyclass %}{{ block.super }} app-{{ opts.app_label }} model-{{ opts.model_name }} change-form{% endblock %}

{% block breadcrumbs %}
<div class="breadcrumbs">
<a href="{% url 'admin:index' %}">{% translate 'Home' %}</a>
&rsaquo; <a href="{% url 'admin:app_list' app_label=opts.app_label %}">{{ opts.app_config.verbose_name }}</a>
&rsaquo; <a href="{% url 'admin:grading_repository_changelist' %}">{{ opts.verbose_name_plural|capfirst }}</a>
&rsaquo; {% translate 'Change Branch' %}
</div>
{% endblock %}

{% block content %}
<div id="content-main">
    <form method="post" id="{{ opts.model_name }}_form" novalidate>
        {% csrf_token %}
        <fieldset class="module aligned">
            <div class="form-row">
                <div class="field-box">
                    <label for="branch">{% translate 'Branch' %}:</label>
                    <select name="branch" id="branch">
                        {% for branch in branches %}
                            <option value="{{ branch }}" {% if branch == current_branch %}selected{% endif %}>
                                {{ branch }}
                            </option>
                        {% endfor %}
                    </select>
                </div>
            </div>
        </fieldset>
        <div class="submit-row">
            <input type="submit" value="{% translate 'Change Branch' %}" class="default">
            <a href="{% url 'admin:grading_repository_changelist' %}" class="button cancel-link">{% translate 'Cancel' %}</a>
        </div>
    </form>
</div>
{% endblock %}

{% block extrahead %}
    {{ block.super }}
    <style>
        .field-box {
            margin-bottom: 15px;
        }
        .field-box label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .field-box select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
    </style>
{% endblock %}'''

write_template('templates/admin/grading/repository/change_branch.html', change_branch_content)

# ssh_key_file_input.html
ssh_key_file_input_content = '''{% include "django/forms/widgets/clearable_file_input.html" %}
<div class="ssh-key-file-input-wrapper">
    <button type="button" class="button select-ssh-key">上传 SSH 私钥文件</button>
    <span class="ssh-key-file-name"></span>
</div>'''

write_template('templates/admin/widgets/ssh_key_file_input.html', ssh_key_file_input_content)

print("Successfully created admin templates") 
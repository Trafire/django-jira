// (Markup info at)
// # (https://jira.atlassian.com/secure/WikiRendererHelpAction.jspa?section=all)

h1. {{exc_name}}

||Heading||Data||
| Error Type | {{exc}} |
| Url Path | {{request.get_full_path()}} |
| Query Parameters |{%for parameter in parameters%}* {{parameter}}{% endfor %}|

h2. Stack

{% for frame in stacktrace %}
    ||section||data||
    |filename|{{frame.filename}}|
    |name|{{frame.name}}|
    |lineno|{{frame.lineno}}|
    |locals|{{frame.locals}}|
    |request|{{frame.request}}|
    |username|{{frame.username}}|
{% endfor %}




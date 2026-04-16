{{/*
Re-export common library templates for the app-go chart.
These wrap the common-lib definitions so they can be used
with chart-specific names if needed.
*/}}

{{- define "app-go.name" -}}
{{- include "common.name" . }}
{{- end }}

{{- define "app-go.fullname" -}}
{{- include "common.fullname" . }}
{{- end }}

{{- define "app-go.chart" -}}
{{- include "common.chart" . }}
{{- end }}

{{- define "app-go.labels" -}}
{{- include "common.labels" . }}
{{- end }}

{{- define "app-go.selectorLabels" -}}
{{- include "common.selectorLabels" . }}
{{- end }}

{{/*
Common environment variables (named template for DRY principle)
*/}}
{{- define "app-go.envVars" -}}
- name: APP_ENV
  value: {{ .Values.environment | default "development" | quote }}
- name: LOG_LEVEL
  value: {{ .Values.logLevel | default "info" | quote }}
{{- end }}

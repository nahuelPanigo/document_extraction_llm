# Documentación de la API: Document Extractor Services

Esta API permite procesar archivos PDF o DOCX para extraer metadatos estructurados mediante una arquitectura modular con servicios de extracción y LLM.

---

##  Arquitectura General

![Flujo de procesamiento](diagram_flujo_api.png)

---

##  Flujo General

1. El archivo es recibido por el **orchestrator**.
2. Se determina el tipo de documento o se pasa por parametro.
3. Se pasa por el extractor de texto (si no se pasa el tipo) 
4. se obtiene el tipo pasandole el texto a nuestro modelo de tipo  (si no se pasa el tipo) 
5. Se pasa por el extractor de texto con tags
6. Se construye un prompt para el modelo LLM.
7. Se retornan los metadatos estructurados.

---

## Endpoint: `POST /upload` (Orchestrator)

**URL:** `{BASE_URL}:8000/upload`

### Headers

- `Authorization`: Bearer token
- `Content-Type`: multipart/form-data

### Body (form-data)

| Campo          | Tipo       | Requerido | Descripción                                                        |
|----------------|------------|-----------|--------------------------------------------------------------------|
| `file`         | archivo    | SI	  | Documento `.pdf` o `.docx`                                         |
| `normalization`| boolean    | NO        | Limpieza del texto (`true` por defecto)                            |
| `type`         | Enum       |NO         | `Libro`, `Tesis`, `Articulo`, `General`                            |

### Ejemplos de Curl

* Only File:
```bash
curl --location 'http://localhost:8000/upload' \
--header 'Authorization: Bearer <tu_token>' \
--header 'Content-Type: multipart/form-data' \
--form 'file=@"/path/to/file"' \
```
* File and Normalization
```bash
curl --location 'http://localhost:8000/upload' \
--header 'Authorization: Bearer <tu_token>' \
--header 'Content-Type: multipart/form-data' \
--form 'file=@"/path/to/file"' \
--form 'normalization="true"' 
```

* File Normalization and type

```bash
curl --location 'http://localhost:8000/upload' \
--header 'Authorization: Bearer <tu_token>' \
--header 'Content-Type: multipart/form-data' \
--form 'file=@"/path/to/file"' \
--form 'normalization="true"' \
--form 'type="Libro"'
```

### Respuesta Exitosa

```json

{
	"success": true,
	"data": {
		"language": "es",
		"title": "Cambio climático y seguridad alimentaria global: Oportunidades y amenazas para el sector rural argentino",
		"creator": "E F. V.",
		"subject": "Agricultura,silvicultura y pesca",
		"rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
		"rightsurl": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
		"date": "2022-01-01",
		"originPlaceInfo": "Facultad de Ciencias Agrarias y Forestales",
		"codirector": "Dra. Carolina Pérez",
		"director": "Emanuel Víctor",
		"degree.grantor": "Universidad Nacional de La Plata",
		"degree.name": "Especialista en Agronomía y Forestales"
	},
	"error": null
}
```

### Errores Comunes

- `415`: Formato no soportado (solo PDF o DOCX)
- `400`: Parámetros faltantes o mal formateados
- `500`: Error inesperado

---


## Endpoints de los demas servicios consumidos por el orchestrator


## Service Extractor

## Endpoint: `POST /extract` (Extractor Plano)

**URL:** `{BASE_URL}:8001/extract`

### Headers

- `Authorization`: Bearer token
- `Content-Type`: multipart/form-data

### Body (form-data)

| Campo          | Tipo       | Requerido | Descripción                                                        |
|----------------|------------|-----------|--------------------------------------------------------------------|
| `file`         | archivo    | SI	  | Documento `.pdf` o `.docx`                                         |
| `normalization`| boolean    | NO        | Limpieza del texto (`true` por defecto)                            |


### Ejemplos de Curl

* Only file

```bash
curl --location 'http://localhost:8001/extract' \
--header 'Content-Type: multipart/form-data' \
--header 'Authorization: Bearer <tu_token>' \
--form 'file=@"/path/to/file"' 
```

* with File and Normalization

```bash
curl --location 'http://localhost:8001/extract' \
--header 'Content-Type: multipart/form-data' \
--header 'Authorization: Bearer <tu_token>' \
--form 'file=@"/path/to/file"' \
--form 'normalization="true"'
```


### Respuesta

```json
{
  "success": true,
  "data": {
    "text": "Texto extraído..."
  }
}
```

### Errores Comunes

- `415`: Formato no soportado (solo PDF o DOCX)
- `400`: Parámetros faltantes o mal formateados

---

##  Endpoint: `POST /extract-with-tags` (Extractor con XML)

**URL:** `{BASE_URL}:8001/extract-with-tags`

Igual que el extractor plano, pero con salida en HTML/XML.

---

## Service llm-service


## Endpoint: `POST /consume-llm` (LLM Service)

**URL:** `{BASE_URL}:8002/consume-llm`

### Headers

- `Authorization`: Bearer token
- `Content-Type`: application/json 

### Body (form-data)

| Campo          | Tipo       | Requerido | Descripción                                                        |
|----------------|------------|-----------|--------------------------------------------------------------------|
| `text`         | string     | SI	  | texto extraido del documento + prompt                              |

### Body (JSON)

```json
{
  "text": "<prompt y texto con tags XML>"
}
```

### Ejemplos de Curl

```bash
curl --location 'http://localhost:8002/consume-llm' \
--header 'Content-Type: multipart/form-data' \
--header 'Authorization: Bearer <tu_token>' \
--data '{"text" : "texto"}'
```



### Respuesta

```json
{
  "success": true,
  "data": {
    "text": "{ metadata json }"
  }
}
```

### Errores Comunes

- `500`: Error inesperado
- `400`: Parámetros faltantes o mal formateados

---

## Variables de entorno sugeridas

```env
BASE_URL=http://localhost
ORCHSTRATOR_TOKEN=<token>
EXTRACTOR_TOKEN=<token>
LLM_SERVICE_TOKEN=<token>
```

---
\

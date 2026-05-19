# Plataforma de Tutorías para Estudiantes (CU2)

## 📌 Descripción del Proyecto

La **Plataforma de Tutorías para Estudiantes** es una aplicación de escritorio desarrollada en Python que nace con el objetivo de solucionar una problemática real dentro del campus universitario **CU2**: la desconexión e informalidad al momento de buscar o impartir asesorías académicas. 

A menudo, los alumnos que necesitan regularizarse o resolver dudas en materias complejas no encuentran canales oficiales para conectar con personas capacitadas, mientras que los estudiantes con excelente rendimiento no disponen de un medio organizado para ofrecer su apoyo. Esta desconexión puede derivar en un bajo rendimiento académico o en el abandono de asignaturas.

Este sistema centraliza y formaliza todo el proceso. A través de una arquitectura robusta basada en el paradigma de **Programación Orientada a Objetos (POO)** y una interfaz gráfica intuitiva, la aplicación permite gestionar de manera eficiente el registro de usuarios, el control de agendas en tiempo real, la asignación lógica de citas y el análisis estadístico del impacto académico del programa.

---

## 🚀 Funcionalidades Principales

El sistema segmenta las herramientas y vistas según el rol del usuario autenticado:

### 👨‍🎓 Módulo del Estudiante
* **Registro y Perfil:** Creación de cuenta especificando datos personales, nivel académico y materias de interés o de mayor dificultad.
* **Búsqueda Avanzada:** Filtros dinámicos para explorar la lista de tutores disponibles según su especialidad académica y horarios.
* **Agenda de Tutorías:** Panel interactivo para solicitar asesorías seleccionando fecha y hora de manera directa.
* **Sistema de Calificación:** Opción de valorar el desempeño del tutor (escala de 0 a 5 estrellas) al concluir cada sesión, fomentando la retroalimentación y la transparencia.

### 👨‍🏫 Módulo del Tutor
* **Gestión de Horarios:** Configuración manual de días, horas de inicio/fin y cupo máximo de alumnos permitidos por sesión.
* **Control de Solicitudes:** Bandeja de entrada para aceptar o rechazar solicitudes de asesorías en tiempo real, actualizando estados lógicos dinámicamente (*Pendiente, Aceptada, Rechazada*).
* **Seguimiento Académico:** Registro de notas y comentarios sobre el progreso de los alumnos atendidos.

### 📊 Módulo de Análisis e Indicadores (Administración)
* **Visualización de Datos:** Generación automatizada de gráficos estadísticos para identificar las asignaturas más solicitadas y los tutores con mayor actividad.
* **Detección de "Cuellos de Botella":** Análisis de tendencias temporales de solicitudes para que la institución identifique qué materias requieren reforzamiento en los planes de estudio.

---

## 🛠️ Tecnologías Utilizadas

La aplicación se construyó utilizando componentes nativos y librerías especializadas de Python para garantizar ligereza y portabilidad:

* **Lenguaje base:** Python
* **Interfaz Gráfica de Usuario (GUI):** `Tkinter` (diseño de ventanas, formularios limpios y menús interactivos).
* **Gestión y Procesamiento de Datos:** `Pandas` (manejo interno de estructuras de datos y registros cotidianos).
* **Visualización de Datos:** `Matplotlib` (renderizado de gráficos estadísticos de barras y tendencias).
* **Lógicas del Sistema:** `datetime` (validación estricta de fechas y horas) y `enum` (control formal de estados).

---

## 🏗️ Arquitectura del Software

El código sigue un diseño limpio y escalable enfocado en buenas prácticas de desarrollo:
* **Herencia y Polimorfismo:** Implementación de una clase base abstracta `Persona` de la cual heredan de manera limpia las clases `Estudiante` y `Tutor`, compartiendo atributos esenciales (nombre, email, contraseña) y reutilizando métodos de inicio de sesión.
* **Encapsulamiento:** Protección de datos sensibles mediante atributos privados y métodos de acceso controlados para la gestión segura de las cuentas.
* **Control de Concurrencia Lógica:** La clase `SesionTutoria` valida matemáticamente que no existan cruces de horarios para un mismo tutor ni sobrecupos en las sesiones agendadas.

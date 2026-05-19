from abc import ABC, abstractmethod
from enum import Enum
import pandas as pd

class EstadoSesion(Enum):
    PENDIENTE = "PENDIENTE"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"
    CANCELADA = "CANCELADA"

class Persona(ABC):
    def __init__(self, id_persona, nombre, email, contrasena):
        self.id_persona = id_persona
        self.nombre = nombre
        self.email = email
        self.contrasena = contrasena
        self.activa = True

    def login(self, email_input, contrasena_input):
        """Valida las credenciales"""
        if self.email == email_input and self.contrasena == contrasena_input:
            if self.activa:
                return True, f"Inicio de sesión exitoso. Bienvenido {self.nombre}."
            else:
                return False, "La cuenta está desactivada."
        return False, "Credenciales incorrectas."

    def actualizar_perfil(self, **kwargs):
        """modificar los datos personales"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return True, "Perfil actualizado correctamente."

    def eliminar_cuenta(self, contrasena_input):
        """dar de baja su perfil"""
        if self.contrasena == contrasena_input:
            self.activa = False
            return True, "La cuenta ha sido eliminada exitosamente."
        return False, "Contraseña incorrecta. No se pudo eliminar la cuenta."

class Estudiante(Persona):
    def __init__(self, id_persona, nombre, email, contrasena, nivel_academico):
        super().__init__(id_persona, nombre, email, contrasena)
        self.nivel_academico = nivel_academico
        self.historial_tutorias = [] 
    
    def solicitar_tutoria(self, sesion):
        """Crea una nueva petición de clase."""
        return sesion.agregar_alumno(self)

    def cancelar_tutoria(self, id_sesion):
        """cancelar una tutoría(PENDIENTE o ACEPTADA)."""
        for tutoria in self.historial_tutorias:
            if tutoria.get('id_sesion') == id_sesion:
                tutoria['estado'] = EstadoSesion.CANCELADA.value
                # En un sistema completo, aquí se notifica a la clase SesionTutoria para restar 'alumnos_inscritos'
                return True, f"Solicitud para la sesión {id_sesion} cancelada exitosamente."
        return False, "No se encontró la tutoría en el historial."

    def obtener_historial_asesorias(self):
        return self.historial_tutorias

    def evaluar_tutoria(self, tutor, id_sesion, estrellas):
        """Asigna una calificación al tutor"""
        if not (0 <= estrellas <= 5):
            return False, "La calificación debe estar entre 0 y 5 estrellas."

        for tutoria in self.historial_tutorias:
            if tutoria.get('id_sesion') == id_sesion:
                tutoria['calificacion_al_tutor'] = estrellas
                tutor.recibir_calificacion(estrellas)
                return True, f"Sesión evaluada con {estrellas} estrellas. ¡Gracias por tu aportación!"
        return False, "Sesión no encontrada en el historial."

class Tutor(Persona):
    def __init__(self, id_persona, nombre, email, contrasena, especialidad, descripcion=""):
        super().__init__(id_persona, nombre, email, contrasena)
        self.especialidad = especialidad
        self.descripcion = descripcion
        self.calificaciones = []
        self.mis_sesiones = []

    @property
    def promedio_estrellas(self):
        if not self.calificaciones:
            return 0.0
        return round(sum(self.calificaciones) / len(self.calificaciones), 1)

    def recibir_calificacion(self, estrellas):
        self.calificaciones.append(estrellas)

    def obtener_mis_tutorias(self):
        """lista de las tutorías impartidas por tutor."""
        datos = []
        for s in self.mis_sesiones:
            datos.append({
                "id_sesion": s.id_sesion,
                "materia": s.tutoria.nombre,
                "dias": s.dias,
                "horario": f"{s.hora_inicio} - {s.hora_final}",
                "cupo_maximo": s.cupo_maximo,
                "alumnos_inscritos": s.alumnos_inscritos,
                "lleno": s.alumnos_inscritos >= s.cupo_maximo
            })
        return datos

    def editar_tutoria(self, id_sesion, nuevos_dias, nueva_hora_inicio, nueva_hora_final):
        """Permite al tutor editar los detalles de su tutoría"""
        for sesion in self.mis_sesiones:
            if sesion.id_sesion == id_sesion:
                sesion.dias = nuevos_dias
                sesion.hora_inicio = nueva_hora_inicio
                sesion.hora_final = nueva_hora_final
                return True, f"Tutoría {id_sesion} actualizada exitosamente."
        return False, "No tienes permiso o no se encontró la sesión."

    def obtener_solicitudes(self, id_sesion):
        """alumnos que están solicitando una sesión"""
        solicitudes = []
        for sesion in self.mis_sesiones:
            if sesion.id_sesion == id_sesion:
                for alumno in sesion.lista_alumnos:
                    # En un modelo real, filtraríamos por estado PENDIENTE dentro del historial del alumno
                    solicitudes.append({
                        "id_alumno": alumno.id_persona,
                        "nombre": alumno.nombre,
                        "nivel": alumno.nivel_academico
                    })
                break
        return solicitudes

    def responder_solicitud(self, sesion, estudiante, aceptar):
        """Acepta o rechaza la solicitud de un alumno"""
        nuevo_estado = EstadoSesion.ACEPTADA if aceptar else EstadoSesion.RECHAZADA
        
        for t in estudiante.historial_tutorias:
            if t['id_sesion'] == sesion.id_sesion:
                t['estado'] = nuevo_estado.value
                accion = "Aceptada" if aceptar else "Rechazada"
                return True, f"Solicitud de {estudiante.nombre} ha sido {accion}."
        return False, "No se encontró la solicitud de este alumno."

class Tutoria:
    def __init__(self, id_materia, nombre, area):
        self.id_materia = id_materia
        self.nombre = nombre
        self.area = area

class SesionTutoria:
    def __init__(self, id_sesion, tutoria, tutor, dias, hora_inicio, hora_final, cupo_maximo):
        self.id_sesion = id_sesion
        self.tutoria = tutoria
        self.tutor = tutor
        self.dias = dias 
        self.hora_inicio = hora_inicio 
        self.hora_final = hora_final 
        self.cupo_maximo = cupo_maximo
        self.alumnos_inscritos = 0
        self.lista_alumnos = []
        
        # Vincular sesión al tutor
        self.tutor.mis_sesiones.append(self)

    def verificar_disponibilidad(self):
        return self.alumnos_inscritos < self.cupo_maximo

    def agregar_alumno(self, estudiante):
        if self.verificar_disponibilidad():
            # Evitar inscripciones duplicadas
            for alumno in self.lista_alumnos:
                if alumno.id_persona == estudiante.id_persona:
                    return False, "El estudiante ya había enviado una solicitud para esta sesión."

            self.lista_alumnos.append(estudiante)
            self.alumnos_inscritos += 1
            estudiante.historial_tutorias.append({
                "id_sesion": self.id_sesion,
                "materia": self.tutoria.nombre,
                "horario": f"{self.dias} {self.hora_inicio}-{self.hora_final}",
                "estado": EstadoSesion.PENDIENTE.value,
                "calificacion_al_tutor": None
            })
            return True, f"Solicitud enviada a {self.tutor.nombre} para la materia {self.tutoria.nombre}."
        else:
            return False, "Lo sentimos, esta tutoría tiene el cupo lleno."

class SistemaTutorias:
    def __init__(self):
        self.usuarios = {} # Diccionario email -> Persona
        self.tutorias = []
        self.sesiones = []
        self.generador_ids_usuarios = 1
        self.generador_ids_sesiones = 1

    def registrar_usuario(self, tipo, nombre, email, contrasena, **kwargs):
        """Registra un nuevo estudiante o tutor"""
        if email in self.usuarios:
            return False, "El email ya está registrado.", None
        
        id_nuevo = self.generador_ids_usuarios
        self.generador_ids_usuarios += 1
        
        if tipo.lower() == 'estudiante':
            nuevo_usuario = Estudiante(id_nuevo, nombre, email, contrasena, kwargs.get('nivel_academico', ''))
        elif tipo.lower() == 'tutor':
            nuevo_usuario = Tutor(id_nuevo, nombre, email, contrasena, kwargs.get('especialidad', ''), kwargs.get('descripcion', ''))
        else:
            return False, "Tipo de usuario inválido.", None
            
        self.usuarios[email] = nuevo_usuario
        return True, "Registro Exitoso.", nuevo_usuario

    def iniciar_sesion(self, email, contrasena):
        usuario = self.usuarios.get(email)
        if usuario:
            exito, mensaje = usuario.login(email, contrasena)
            if exito:
                return True, mensaje, usuario
            return False, mensaje, None
        return False, "Usuario no encontrado.", None

    def crear_tutoria(self, nombre, area):
        """Crea una materia"""
        nueva_tutoria = Tutoria(len(self.tutorias) + 1, nombre, area)
        self.tutorias.append(nueva_tutoria)
        return nueva_tutoria

    def agendar_sesion(self, tutoria, tutor, dias, hora_inicio, hora_final, cupo_maximo):
        id_sesion = self.generador_ids_sesiones
        self.generador_ids_sesiones += 1
        nueva_sesion = SesionTutoria(id_sesion, tutoria, tutor, dias, hora_inicio, hora_final, cupo_maximo)
        self.sesiones.append(nueva_sesion)
        return nueva_sesion

    def buscar_sesiones(self, query=""):
        """Busca sesiones por materia o nombre de tutor"""
        resultados = []
        for s in self.sesiones:
            if not query or query.lower() in s.tutoria.nombre.lower() or query.lower() in s.tutor.nombre.lower():
                resultados.append({
                    "id_sesion": s.id_sesion,
                    "materia": s.tutoria.nombre,
                    "tutor": s.tutor.nombre,
                    "estrellas_tutor": s.tutor.promedio_estrellas,
                    "dias": s.dias,
                    "horario": f"{s.hora_inicio} - {s.hora_final}",
                    "cupo_actual": s.alumnos_inscritos,
                    "cupo_maximo": s.cupo_maximo,
                    "lleno": s.alumnos_inscritos >= s.cupo_maximo
                })
        return resultados

    def obtener_sesion_por_id(self, id_sesion):
        for s in self.sesiones:
            if s.id_sesion == id_sesion:
                return s
        return None

    def generar_reporte_materias_dataframe(self):
        if not self.sesiones: return None
        data = [{"Materia": s.tutoria.nombre, "Alumnos": s.alumnos_inscritos} for s in self.sesiones]
        df = pd.DataFrame(data)
        return df.groupby('Materia')['Alumnos'].sum().sort_values(ascending=False).reset_index()

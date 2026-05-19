from BackendTutorias import *

import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import pandas as pd

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DIRECTORIO_TRABAJO = os.path.dirname(os.path.abspath(__file__))
CSV_USUARIOS = os.path.join(DIRECTORIO_TRABAJO, "usuarios_data.csv")
CSV_SESIONES = os.path.join(DIRECTORIO_TRABAJO, "sesiones_data.csv")
CSV_HISTORIAL = os.path.join(DIRECTORIO_TRABAJO, "historial_tutorias_data.csv")

class AppTutoriasPersistente(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Sistema de Visualización de Tutorías con Persistencia")
        
        # CORRECCIÓN: Definimos un tamaño base y retrasamos el maximizado 
        # para que customtkinter calcule bien las dimensiones del Login.
        self.geometry("1200x700")
        self.after(10, lambda: self.state("zoomed"))
        
        self.configure(fg_color="#1a2332")
        
        self.sistema = SistemaTutorias()
        self.usuario_actual = None
        
        self.inicializar_y_cargar_datos()
        
        self.contenedor_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.contenedor_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.mostrar_login()

    def inicializar_y_cargar_datos(self):
        if os.path.exists(CSV_USUARIOS) and os.path.exists(CSV_SESIONES):
            self.cargar_datos_desde_csv()
        else:
            self.crear_plantillas_vacias()

    def crear_plantillas_vacias(self):
        pd.DataFrame(columns=["id_persona","tipo","nombre","email","contrasena","activa","campo_extra","descripcion"]).to_csv(CSV_USUARIOS, index=False)
        pd.DataFrame(columns=["id_sesion","materia_nombre","materia_area","tutor_email","dias","hora_inicio","hora_final","cupo_maximo","alumnos_inscritos"]).to_csv(CSV_SESIONES, index=False)
        pd.DataFrame(columns=["alumno_email","id_sesion","materia","horario","estado","calificacion_al_tutor"]).to_csv(CSV_HISTORIAL, index=False)

    def calcular_siguiente_id_disponible(self):
        ids_actuales = {s.id_sesion for s in self.sistema.sesiones}
        candidato = 1
        while candidato in ids_actuales:
            candidato += 1
        return candidato

    def guardar_datos_a_csv(self):
        u_list = []
        for email, p in self.sistema.usuarios.items():
            tipo = 'estudiante' if isinstance(p, Estudiante) else 'tutor'
            extra = p.nivel_academico if tipo == 'estudiante' else p.especialidad
            u_list.append({
                "id_persona": p.id_persona, "tipo": tipo, "nombre": p.nombre, 
                "email": p.email, "contrasena": p.contrasena, "activa": p.activa,
                "campo_extra": extra, "descripcion": getattr(p, 'descripcion', '')
            })
        pd.DataFrame(u_list).to_csv(CSV_USUARIOS, index=False)

        s_list = []
        for s in self.sistema.sesiones:
            s_list.append({
                "id_sesion": s.id_sesion, "materia_nombre": s.tutoria.nombre, "materia_area": s.tutoria.area,
                "tutor_email": s.tutor.email, "dias": s.dias, "hora_inicio": s.hora_inicio,
                "hora_final": s.hora_final, "cupo_maximo": s.cupo_maximo, "alumnos_inscritos": s.alumnos_inscritos
            })
        pd.DataFrame(s_list).to_csv(CSV_SESIONES, index=False)

        h_list = []
        for email, p in self.sistema.usuarios.items():
            if isinstance(p, Estudiante):
                for tut in p.historial_tutorias:
                    h_list.append({
                        "alumno_email": p.email, "id_sesion": tut["id_sesion"],
                        "materia": tut["materia"], "horario": tut["horario"],
                        "estado": tut["estado"], "calificacion_al_tutor": tut["calificacion_al_tutor"]
                    })
        pd.DataFrame(h_list).to_csv(CSV_HISTORIAL, index=False)

    def cargar_datos_desde_csv(self):
        df_u = pd.read_csv(CSV_USUARIOS)
        df_s = pd.read_csv(CSV_SESIONES)
        
        if os.path.exists(CSV_HISTORIAL) and os.path.getsize(CSV_HISTORIAL) > 0:
            try:
                df_h = pd.read_csv(CSV_HISTORIAL)
            except pd.errors.EmptyDataError:
                df_h = pd.DataFrame()
        else:
            df_h = pd.DataFrame()

        for _, row in df_u.iterrows():
            if row['tipo'] == 'estudiante':
                u = Estudiante(int(row['id_persona']), row['nombre'], row['email'], str(row['contrasena']), row['campo_extra'])
            else:
                u = Tutor(int(row['id_persona']), row['nombre'], row['email'], str(row['contrasena']), row['campo_extra'], row['descripcion'])
            u.activa = bool(row['activa'])
            self.sistema.usuarios[row['email']] = u
            if int(row['id_persona']) >= self.sistema.generador_ids_usuarios:
                self.sistema.generador_ids_usuarios = int(row['id_persona']) + 1

        for _, row in df_s.iterrows():
            tutor_email = row['tutor_email']
            if tutor_email not in self.sistema.usuarios:
                continue
            tutor_obj = self.sistema.usuarios[tutor_email]
            tutoria_obj = next((m for m in self.sistema.tutorias if m.nombre == row['materia_nombre']), None)
            if not tutoria_obj:
                tutoria_obj = self.sistema.crear_tutoria(row['materia_nombre'], row['materia_area'])
            
            s = SesionTutoria(int(row['id_sesion']), tutoria_obj, tutor_obj, str(row['dias']), row['hora_inicio'], row['hora_final'], int(row['cupo_maximo']))
            s.alumnos_inscritos = int(row['alumnos_inscritos'])
            self.sistema.sesiones.append(s)
            if s not in tutor_obj.mis_sesiones:
                tutor_obj.mis_sesiones.append(s)

        if not df_h.empty:
            for _, row in df_h.iterrows():
                correo_alumno = row['alumno_email']
                if correo_alumno not in self.sistema.usuarios:
                    continue
                    
                al_obj = self.sistema.usuarios[correo_alumno]
                ses_obj = self.sistema.obtener_sesion_por_id(int(row['id_sesion']))
                
                if ses_obj and al_obj not in ses_obj.lista_alumnos:
                    if row['estado'] == 'ACEPTADA':
                        ses_obj.lista_alumnos.append(al_obj)
                
                calif = None if pd.isna(row['calificacion_al_tutor']) else int(row['calificacion_al_tutor'])
                
                al_obj.historial_tutorias.append({
                    "id_sesion": int(row['id_sesion']), "materia": row['materia'],
                    "horario": row['horario'], "estado": row['estado'],
                    "calificacion_al_tutor": calif
                })
                if calif is not None and ses_obj:
                    ses_obj.tutor.recibir_calificacion(calif)

    def limpiar_contenedor(self):
        for widget in self.contenedor_principal.winfo_children(): 
            widget.destroy()

    def mostrar_login(self):
        self.limpiar_contenedor()
        panel_login = ctk.CTkFrame(self.contenedor_principal, fg_color="#212e42", corner_radius=20, width=420, height=450)
        panel_login.place(relx=0.5, rely=0.5, anchor="center")
        panel_login.pack_propagate(False)
        
        ctk.CTkLabel(panel_login, text="Inicio de Sesión", font=("Arial", 24, "bold"), text_color="#ff5252").pack(pady=(25, 15))
        
        self.var_rol = tk.StringVar(value="Estudiante")
        
        rb_estudiante = ctk.CTkRadioButton(panel_login, text="Estudiante", variable=self.var_rol, value="Estudiante", fg_color="#2b5797")
        rb_estudiante.pack(pady=2)
        rb_tutor = ctk.CTkRadioButton(panel_login, text="Tutor", variable=self.var_rol, value="Tutor", fg_color="#2b5797")
        rb_tutor.pack(pady=2)
        
        ctk.CTkLabel(panel_login, text="email:", anchor="w").pack(fill="x", padx=45, pady=(15, 2))
        ent_email = ctk.CTkEntry(panel_login, placeholder_text="@gmail.com", fg_color="#1a2332", border_color="#2d3d56", corner_radius=10)
        ent_email.pack(fill="x", padx=45)
        
        ctk.CTkLabel(panel_login, text="contraseña:", anchor="w").pack(fill="x", padx=45, pady=(10, 2))
        ent_contra = ctk.CTkEntry(panel_login, placeholder_text="contraseña", show="*", fg_color="#1a2332", border_color="#2d3d56", corner_radius=10)
        ent_contra.pack(fill="x", padx=45)
        
        def ejecutar_login():
            rol_seleccionado = self.var_rol.get()
            correo_ingresado = ent_email.get()
            
            if correo_ingresado in self.sistema.usuarios:
                objeto_usuario = self.sistema.usuarios[correo_ingresado]
                
                if rol_seleccionado == "Estudiante" and not isinstance(objeto_usuario, Estudiante):
                    messagebox.showerror("Error de Acceso", "El correo ingresado no pertenece a una cuenta de Estudiante.")
                    return
                elif rol_seleccionado == "Tutor" and not isinstance(objeto_usuario, Tutor):
                    messagebox.showerror("Error de Acceso", "El correo ingresado no pertenece a una cuenta de Tutor.")
                    return
            
            exito, msg, user = self.sistema.iniciar_sesion(correo_ingresado, ent_contra.get())
            if exito:
                self.usuario_actual = user
                messagebox.showinfo("Operación Exitosa", msg)
                if isinstance(user, Estudiante):
                    self.mostrar_panel_estudiante()
                else:
                    self.mostrar_panel_tutor()
            else:
                messagebox.showerror("Error", msg)

        ctk.CTkButton(panel_login, text="Ingresar", fg_color="#2b5797", hover_color="#3b71ca", corner_radius=12, command=ejecutar_login).pack(pady=(25, 10))
        ctk.CTkButton(panel_login, text="¿No tienes cuenta? Regístrate", fg_color="transparent", text_color="#3b71ca", command=self.mostrar_registro).pack()

    def mostrar_registro(self):
        self.limpiar_contenedor()
        panel_reg = ctk.CTkFrame(self.contenedor_principal, fg_color="#212e42", corner_radius=20, width=450, height=480)
        panel_reg.place(relx=0.5, rely=0.5, anchor="center")
        panel_reg.pack_propagate(False)
        
        ctk.CTkLabel(panel_reg, text="Formulario de Registro", font=("Arial", 22, "bold"), text_color="#ff5252").pack(pady=15)
        tipo_var = tk.StringVar(value="estudiante")
        ctk.CTkRadioButton(panel_reg, text="Estudiante", variable=tipo_var, value="estudiante").pack(pady=2)
        ctk.CTkRadioButton(panel_reg, text="Tutor", variable=tipo_var, value="tutor").pack(pady=2)
        
        ctk.CTkLabel(panel_reg, text="Nombre Completo:").pack()
        ent_nom = ctk.CTkEntry(panel_reg, fg_color="#1a2332", border_color="#2d3d56", width=300)
        ent_nom.pack()
        
        ctk.CTkLabel(panel_reg, text="Email:").pack()
        ent_em = ctk.CTkEntry(panel_reg, fg_color="#1a2332", border_color="#2d3d56", width=300)
        ent_em.pack()
        
        ctk.CTkLabel(panel_reg, text="Contraseña:").pack()
        ent_co = ctk.CTkEntry(panel_reg, show="*", fg_color="#1a2332", border_color="#2d3d56", width=300)
        ent_co.pack()
        
        ctk.CTkLabel(panel_reg, text="Dato Extra (Nivel / Especialidad):").pack()
        ent_ex = ctk.CTkEntry(panel_reg, fg_color="#1a2332", border_color="#2d3d56", width=300)
        ent_ex.pack()

        def registrar_y_guardar():
            t = tipo_var.get()
            kw = {'nivel_academico': ent_ex.get()} if t == 'estudiante' else {'especialidad': ent_ex.get(), 'descripcion': 'Tutor Ofertante'}
            exito, msg, _ = self.sistema.registrar_usuario(t, ent_nom.get(), ent_em.get(), ent_co.get(), **kw)
            if exito:
                self.guardar_datos_a_csv() 
                messagebox.showinfo("Operación Exitosa", "Registro Exitoso.")
                self.mostrar_login()
            else:
                messagebox.showerror("Error", msg)

        ctk.CTkButton(panel_reg, text="Registrar", fg_color="#2b5797", command=registrar_y_guardar).pack(pady=15)
        ctk.CTkButton(panel_reg, text="Volver", fg_color="transparent", command=self.mostrar_login).pack()

    def lanzar_editar_perfil(self, callback_recarga):
        user = self.usuario_actual
        pop = ctk.CTkToplevel(self)
        pop.geometry("380x450")
        pop.title("Editar Perfil de Usuario")
        pop.attributes("-topmost", True)
        
        ctk.CTkLabel(pop, text="Modificar Datos Personales", font=("Arial", 16, "bold"), text_color="#ff5252").pack(pady=15)
        
        ctk.CTkLabel(pop, text="Nombre Completo:").pack()
        e_nom = ctk.CTkEntry(pop, width=250); e_nom.pack(pady=2); e_nom.insert(0, user.nombre)
        
        ctk.CTkLabel(pop, text="Correo Electrónico (Email):").pack()
        e_em = ctk.CTkEntry(pop, width=250); e_em.pack(pady=2); e_em.insert(0, user.email)
        
        ctk.CTkLabel(pop, text="Nueva Contraseña:").pack()
        e_co = ctk.CTkEntry(pop, width=250); e_co.pack(pady=2); e_co.insert(0, user.contrasena)
        
        def procesar_actualizacion():
            nuevo_email = e_em.get()
            if nuevo_email != user.email and nuevo_email in self.sistema.usuarios:
                messagebox.showerror("Error", "Ese correo ya está registrado por otro usuario.")
                return
                
            antiguo_email = user.email
            user.nombre = e_nom.get()
            user.contrasena = e_co.get()
            user.email = nuevo_email
            
            if antiguo_email != nuevo_email:
                self.sistema.usuarios[nuevo_email] = self.sistema.usuarios.pop(antiguo_email)
                
            self.guardar_datos_a_csv()
            messagebox.showinfo("Éxito", "Perfil actualizado con éxito.")
            pop.destroy()
            callback_recarga()

        def procesar_eliminacion():
            if messagebox.askyesno("Eliminar Cuenta", "Esta acción es irreversible, se borrarán todos tus datos."):
                email_borrar = user.email
                if email_borrar in self.sistema.usuarios:
                    self.sistema.usuarios.pop(email_borrar)
                
                if isinstance(user, Estudiante):
                    for s in self.sistema.sesiones:
                        if user in s.lista_alumnos:
                            s.lista_alumnos.remove(user)
                            s.alumnos_inscritos = len(s.lista_alumnos)
                else:
                    sesiones_a_mantener = []
                    for s in self.sistema.sesiones:
                        if s.tutor.email == email_borrar:
                            for k, u in self.sistema.usuarios.items():
                                if isinstance(u, Estudiante):
                                    u.historial_tutorias = [tut for tut in u.historial_tutorias if tut["id_sesion"] != s.id_sesion]
                        else:
                            sesiones_a_mantener.append(s)
                    self.sistema.sesiones = sesiones_a_mantener
                
                self.guardar_datos_a_csv()
                messagebox.showinfo("Cuenta Eliminada", "Tu cuenta ha sido dada de baja.")
                pop.destroy()
                self.mostrar_login()

        ctk.CTkButton(pop, text="Guardar Cambios", fg_color="#2b5797", command=procesar_actualizacion).pack(pady=15)
        ctk.CTkButton(pop, text="Eliminar mi Cuenta", fg_color="#ff5252", command=procesar_eliminacion).pack(pady=5)

    def mostrar_panel_estudiante(self):
        self.limpiar_contenedor()
        user = self.usuario_actual
        
        header = ctk.CTkFrame(self.contenedor_principal, fg_color="#212e42", corner_radius=15, height=75)
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="Panel Estudiante", font=("Arial", 20, "bold"), text_color="#ff5252").pack(side="left", padx=20)
        
        lbl_info = ctk.CTkLabel(header, text=f"|  Estudiante: {user.nombre}  |  Nivel: {user.nivel_academico}", font=("Arial", 13))
        lbl_info.pack(side="left", padx=10)
        
        ctk.CTkButton(header, text="Cerrar Sesión", fg_color="#ff5252", width=100, command=self.mostrar_login).pack(side="right", padx=20)
        ctk.CTkButton(header, text="Editar Perfil", fg_color="#2b5797", width=100, command=lambda: self.lanzar_editar_perfil(self.mostrar_panel_estudiante)).pack(side="right", padx=5)

        tabview = ctk.CTkTabview(self.contenedor_principal, fg_color="#212e42", segmented_button_selected_color="#2b5797")
        tabview.pack(fill="both", expand=True)
        tab_b = tabview.add("Buscar y Solicitar")
        tab_h = tabview.add("Mi Historial / Calificar")
        
        ent_buscar = ctk.CTkEntry(tab_b, placeholder_text="Buscar tutoría o materia...", width=400)
        ent_buscar.pack(pady=5)
        scr_b = ctk.CTkScrollableFrame(tab_b, fg_color="#1a2332")
        scr_b.pack(fill="both", expand=True, padx=10, pady=5)
        
        def render_busqueda():
            for w in scr_b.winfo_children(): 
                w.destroy()
                
            ahora = datetime.now()
            
            for ses in self.sistema.buscar_sesiones(ent_buscar.get()):
                s_obj = self.sistema.obtener_sesion_por_id(ses['id_sesion'])
                if not s_obj:
                    continue
                
                try:
                    fecha_sesion = datetime.strptime(s_obj.dias, "%Y-%m-%d")
                    if s_obj.hora_inicio == "00:00":
                        if fecha_sesion.date() < ahora.date():
                            continue
                    else:
                        h_split = s_obj.hora_inicio.split(":")
                        fecha_completa_sesion = fecha_sesion.replace(hour=int(h_split[0]), minute=int(h_split[1]))
                        if fecha_completa_sesion < (ahora + timedelta(hours=24)):
                            continue
                except ValueError:
                    pass
                
                item = ctk.CTkFrame(scr_b, fg_color="#212e42", corner_radius=10)
                item.pack(fill="x", padx=10, pady=5)
                
                txt = f"Materia: {ses['materia']}  |  Tutor: {ses['tutor']} (⭐ {ses['estrellas_tutor']} estrellas)\nFecha Programada: {s_obj.dias} en el rango [{ses['horario']}]\nCupo Registrado: {ses['cupo_actual']}/{ses['cupo_maximo']}"
                ctk.CTkLabel(item, text=txt, justify="left").pack(side="left", padx=15, pady=10)
                
                def solicitar_click(id_s=ses['id_sesion']):
                    s_real = self.sistema.obtener_sesion_por_id(id_s)
                    registro_existente = next((t for t in user.historial_tutorias if t["id_sesion"] == id_s), None)
                    if registro_existente:
                        registro_existente["estado"] = "PENDIENTE"
                        messagebox.showinfo("Operación Exitosa", f"Has vuelto a solicitar la tutoría de {s_real.tutoria.nombre}.")
                    else:
                        user.solicitar_tutoria(s_real)
                        messagebox.showinfo("Operación Exitosa", f"Solicitud enviada para {s_real.tutoria.nombre}.")
                    
                    self.guardar_datos_a_csv() 
                    render_busqueda()
                
                registro_h = next((t for t in user.historial_tutorias if t["id_sesion"] == ses['id_sesion']), None)
                
                if registro_h and registro_h['estado'] in ['PENDIENTE', 'ACEPTADA']:
                    ctk.CTkButton(item, text="Solicitado", fg_color="#2d3d56", state="disabled", width=90).pack(side="right", padx=15)
                elif ses['lleno']:
                    ctk.CTkButton(item, text="Lleno", fg_color="grey", state="disabled", width=90).pack(side="right", padx=15)
                else:
                    ctk.CTkButton(item, text="Solicitar", fg_color="#2b5797", width=90, command=solicitar_click).pack(side="right", padx=15)

        ent_buscar.bind("<KeyRelease>", lambda e: render_busqueda())
        render_busqueda()

        scr_h = ctk.CTkScrollableFrame(tab_h, fg_color="#1a2332")
        scr_h.pack(fill="both", expand=True, padx=10, pady=10)
        
        def render_historial():
            for w in scr_h.winfo_children(): 
                w.destroy()
            
            ahora = datetime.now()
            for tut in user.obtener_historial_asesorias():
                ses_obj = self.sistema.obtener_sesion_por_id(tut['id_sesion'])
                if not ses_obj:
                    continue
                
                tutoria_ya_paso = False
                try:
                    fecha_tutoria = datetime.strptime(ses_obj.dias, "%Y-%m-%d")
                    if ahora.date() > fecha_tutoria.date():
                        tutoria_ya_paso = True
                except ValueError:
                    pass

                item = ctk.CTkFrame(scr_h, fg_color="#212e42", corner_radius=10)
                item.pack(fill="x", padx=10, pady=5)
                
                calif_str = f"⭐ {tut['calificacion_al_tutor']}" if tut['calificacion_al_tutor'] else "Sin Calificar"
                txt = f"Materia: {tut['materia']}  |  Horario: {tut['horario']}\nEstado de Solicitud: {tut['estado']}  |  Tu Evaluación: {calif_str}"
                ctk.CTkLabel(item, text=txt, justify="left").pack(side="left", padx=15, pady=10)
                
                if tutoria_ya_paso:
                    if tut['estado'] == 'ACEPTADA' and tut['calificacion_al_tutor'] is None:
                        def lanzar_calificar(id_s=tut['id_sesion']):
                            pop = ctk.CTkToplevel(self)
                            pop.geometry("320x200")
                            pop.title("Calificar Sesión")
                            pop.attributes("-topmost", True)
                            
                            ctk.CTkLabel(pop, text="Evalúa las Estrellas (0 al 5)", font=("Arial", 14, "bold")).pack(pady=15)
                            sld = ctk.CTkSlider(pop, from_=0, to=5, number_of_steps=5)
                            sld.pack(pady=10)
                            sld.set(5)
                            
                            def guardar_calif():
                                estrellas = int(sld.get())
                                s_real = self.sistema.obtener_sesion_por_id(id_s)
                                user.evaluar_tutoria(s_real.tutor, id_s, estrellas)
                                self.guardar_datos_a_csv() 
                                messagebox.showinfo("Aportación", "¡Gracias por tu aportación!")
                                pop.destroy()
                                render_historial()
                            
                            ctk.CTkButton(pop, text="Enviar Calificación", fg_color="#2b5797", command=guardar_calif).pack(pady=10)
                        
                        ctk.CTkButton(item, text="Calificar Tutor", fg_color="green", width=110, command=lanzar_calificar).pack(side="right", padx=15)
                else:
                    if tut['estado'] in ['PENDIENTE', 'ACEPTADA']:
                        def cancelar_click(id_s=tut['id_sesion']):
                            user.cancelar_tutoria(id_s)
                            reg = next((t for t in user.historial_tutorias if t["id_sesion"] == id_s), None)
                            if reg:
                                reg["estado"] = "CANCELADA"
                                
                            self.guardar_datos_a_csv() 
                            messagebox.showinfo("Cancelado", "Solicitud cancelada.")
                            render_historial()
                        ctk.CTkButton(item, text="Cancelar", fg_color="#ff5252", width=90, command=cancelar_click).pack(side="right", padx=10)

        tabview.configure(command=lambda: render_historial() if tabview.get() == "Mi Historial / Calificar" else render_busqueda())
        render_historial()

    def mostrar_panel_tutor(self):
        self.limpiar_contenedor()
        tutor = self.usuario_actual
        
        header = ctk.CTkFrame(self.contenedor_principal, fg_color="#212e42", corner_radius=15)
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text=f"Panel Tutor: {tutor.nombre}", font=("Arial", 20, "bold"), text_color="#ff5252").pack(side="left", padx=20, pady=10)
        
        lbl_info_tutor = ctk.CTkLabel(header, text=f"Promedio: ⭐ {tutor.promedio_estrellas} estrellas\nEspecialidad: {tutor.especialidad}", justify="left")
        lbl_info_tutor.pack(side="left", padx=20)
        
        ctk.CTkButton(header, text="Cerrar Sesión", fg_color="#ff5252", width=100, command=self.mostrar_login).pack(side="right", padx=20)
        ctk.CTkButton(header, text="Editar Perfil", fg_color="#2b5797", width=100, command=lambda: self.lanzar_editar_perfil(self.mostrar_panel_tutor)).pack(side="right", padx=5)

        tabview = ctk.CTkTabview(self.contenedor_principal, fg_color="#212e42", segmented_button_selected_color="#2b5797")
        tabview.pack(fill="both", expand=True)
        tab_m = tabview.add("Mis Tutorías Programadas")
        tab_s = tabview.add("Solicitudes de Alumnos")
        
        def lanzar_crear_tutoria():
            pop = ctk.CTkToplevel(self)
            pop.geometry("400x480")
            pop.title("Crear Nueva Tutoría")
            pop.attributes("-topmost", True)
            
            ctk.CTkLabel(pop, text="Nueva Sesión de Tutoría", font=("Arial", 16, "bold"), text_color="#2b5797").pack(pady=10)
            
            ctk.CTkLabel(pop, text="Nombre de la Materia:").pack()
            e_nom = ctk.CTkEntry(pop, width=260); e_nom.pack(pady=2)
            
            ctk.CTkLabel(pop, text="Área de Conocimiento:").pack()
            e_area = ctk.CTkEntry(pop, width=260); e_area.pack(pady=2)
            
            ctk.CTkLabel(pop, text="Fecha (YYYY-MM-DD):").pack()
            e_fecha = ctk.CTkEntry(pop, width=260); e_fecha.pack(pady=2)
            e_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
            
            ctk.CTkLabel(pop, text="Hora Inicio (HH:MM):").pack()
            e_ini = ctk.CTkEntry(pop, width=260); e_ini.pack(pady=2)
            e_ini.insert(0, "00:00")
            
            ctk.CTkLabel(pop, text="Hora Fin (HH:MM):").pack()
            e_fin = ctk.CTkEntry(pop, width=260); e_fin.pack(pady=2)
            e_fin.insert(0, "00:00")
            
            ctk.CTkLabel(pop, text="Cupo Máximo Alumnos:").pack()
            e_cupo = ctk.CTkEntry(pop, width=260); e_cupo.pack(pady=2)
            e_cupo.insert(0, "5")
            
            def guardar_nueva():
                try:
                    cupo_num = int(e_cupo.get())
                except ValueError:
                    messagebox.showerror("Error", "Cupo debe ser un valor numérico entero.")
                    return
                
                tutoria_obj = next((m for m in self.sistema.tutorias if m.nombre == e_nom.get()), None)
                if not tutoria_obj:
                    tutoria_obj = self.sistema.crear_tutoria(e_nom.get(), e_area.get())
                
                id_asignado = self.calcular_siguiente_id_disponible()
                
                nueva_sesion = SesionTutoria(
                    id_asignado,
                    tutoria_obj,
                    tutor,
                    e_fecha.get(),
                    e_ini.get(),
                    e_fin.get(),
                    cupo_num
                )
                
                self.sistema.sesiones.append(nueva_sesion)
                if nueva_sesion not in tutor.mis_sesiones:
                    tutor.mis_sesiones.append(nueva_sesion)
                
                self.guardar_datos_a_csv()
                messagebox.showinfo("Éxito", f"Nueva tutoría #{id_asignado} programada correctamente.")
                pop.destroy()
                render_mis_tutorias()
                
            ctk.CTkButton(pop, text="Programar Tutoría", fg_color="#2b5797", command=guardar_nueva).pack(pady=15)

        ctk.CTkButton(tab_m, text="+ Crear Nueva Tutoría", fg_color="green", font=("Arial", 13, "bold"), command=lanzar_crear_tutoria).pack(pady=10)
        
        scr_m = ctk.CTkScrollableFrame(tab_m, fg_color="#1a2332")
        scr_m.pack(fill="both", expand=True, padx=10, pady=5)
        
        def render_mis_tutorias():
            for w in scr_m.winfo_children(): 
                w.destroy()
            for s in tutor.obtener_mis_tutorias():
                s_real = self.sistema.obtener_sesion_por_id(s['id_sesion'])
                if not s_real:
                    continue
                
                item = ctk.CTkFrame(scr_m, fg_color="#212e42", corner_radius=10)
                item.pack(fill="x", padx=10, pady=5)
                
                info = f"Materia: {s['materia']}  (ID Sesión: #{s['id_sesion']})\nFecha/Días ISO: {s['dias']}  |  Horario: {s['horario']}\nAlumnos inscritos actualmente: {s['alumnos_inscritos']} / {s['cupo_maximo']}"
                
                if s_real.lista_alumnos:
                    lista_al_str = "\nInscritos: " + ", ".join([f"{a.nombre} ({a.email})" for a in s_real.lista_alumnos])
                    info += lista_al_str
                else:
                    info += "\nInscritos: Ninguno"
                
                ctk.CTkLabel(item, text=info, justify="left").pack(side="left", padx=15, pady=10)
                
                def eliminar_click(id_s=s['id_sesion']):
                    if messagebox.askyesno("Confirmar Eliminación", f"¿Seguro que deseas eliminar por completo la tutoría #{id_s}?"):
                        ses_real = self.sistema.obtener_sesion_por_id(id_s)
                        if ses_real in self.sistema.sesiones:
                            self.sistema.sesiones.remove(ses_real)
                        if ses_real in tutor.mis_sesiones:
                            tutor.mis_sesiones.remove(ses_real)
                            
                        for k, u in self.sistema.usuarios.items():
                            if isinstance(u, Estudiante):
                                u.historial_tutorias = [tut for tut in u.historial_tutorias if tut["id_sesion"] != id_s]
                        
                        self.guardar_datos_a_csv()
                        messagebox.showinfo("Eliminado", "Tutoría eliminada sin dejar rastros en el sistema.")
                        render_mis_tutorias()

                def lanzar_editar(id_s=s['id_sesion'], d=s['dias'], h=s['horario']):
                    pop = ctk.CTkToplevel(self)
                    pop.geometry("360x280")
                    pop.title("Editar Detalles de Tutoría")
                    pop.attributes("-topmost", True)
                    
                    ctk.CTkLabel(pop, text="Modificar Horarios", font=("Arial", 14, "bold"), text_color="#ff5252").pack(pady=10)
                    ctk.CTkLabel(pop, text="Fecha ISO (YYYY-MM-DD):").pack()
                    e_d = ctk.CTkEntry(pop, width=220); e_d.pack(); e_d.insert(0, d)
                    
                    h_ini, h_fin = h.split(" - ")
                    ctk.CTkLabel(pop, text="Hora de Inicio:").pack()
                    e_i = ctk.CTkEntry(pop, width=220); e_i.pack(); e_i.insert(0, h_ini)
                    ctk.CTkLabel(pop, text="Hora de Finalización:").pack()
                    e_f = ctk.CTkEntry(pop, width=220); e_f.pack(); e_f.insert(0, h_fin)
                    
                    def guardar_cambios():
                        tutor.editar_tutoria(id_s, e_d.get(), e_i.get(), e_f.get())
                        self.guardar_datos_a_csv() 
                        messagebox.showinfo("Éxito", f"Tutoría {id_s} actualizada exitosamente.")
                        pop.destroy()
                        render_mis_tutorias()
                        
                    ctk.CTkButton(pop, text="Guardar Cambios", fg_color="#2b5797", command=guardar_cambios).pack(pady=15)
                
                ctk.CTkButton(item, text="Eliminar", fg_color="#ff5252", width=80, command=eliminar_click).pack(side="right", padx=10)
                ctk.CTkButton(item, text="Editar Horario", fg_color="#2b5797", width=100, command=lanzar_editar).pack(side="right", padx=5)

        render_mis_tutorias()

        scr_s = ctk.CTkScrollableFrame(tab_s, fg_color="#1a2332")
        scr_s.pack(fill="both", expand=True, padx=10, pady=10)
        
        def render_solicitudes_tutor():
            for w in scr_s.winfo_children(): 
                w.destroy()
            hay_pendientes = False
            
            for s_back in tutor.mis_sesiones:
                s_info = next((item for item in tutor.obtener_mis_tutorias() if item["id_sesion"] == s_back.id_sesion), None)
                if not s_info:
                    continue
                lista_alumnos = tutor.obtener_solicitudes(s_back.id_sesion)
                
                for al in lista_alumnos:
                    al_obj = next(v for k, v in self.sistema.usuarios.items() if v.id_persona == al['id_alumno'])
                    estado_actual = next(t['estado'] for t in al_obj.historial_tutorias if t['id_sesion'] == s_back.id_sesion)
                    
                    if estado_actual == 'PENDIENTE':
                        hay_pendientes = True
                        item = ctk.CTkFrame(scr_s, fg_color="#212e42", corner_radius=10)
                        item.pack(fill="x", padx=10, pady=5)
                        
                        txt = f"Alumno Solicitante: {al['nombre']} ({al['nivel']})\nMateria: {s_info['materia']}  |  Horario de Interés: {s_info['horario']}"
                        ctk.CTkLabel(item, text=txt, justify="left").pack(side="left", padx=15, pady=10)
                        
                        def decidir(alumno=al_obj, sesion=s_back, decision=True):
                            tutor.responder_solicitud(sesion, alumno, aceptar=decision)
                            self.guardar_datos_a_csv() 
                            messagebox.showinfo("Sincronizado", "Respuesta registrada y guardada.")
                            render_solicitudes_tutor()
                            
                        ctk.CTkButton(item, text="Rechazar", fg_color="#ff5252", width=80, command=lambda ao=al_obj, so=s_back: decidir(ao, so, False)).pack(side="right", padx=10)
                        ctk.CTkButton(item, text="Aceptar Alumno", fg_color="#2b5797", width=100, command=lambda ao=al_obj, so=s_back: decidir(ao, so, True)).pack(side="right", padx=10)
            
            if not hay_pendientes:
                ctk.CTkLabel(scr_s, text="No hay peticiones de alumnos en este momento.", font=("Arial", 13)).pack(pady=25)

        tabview.configure(command=lambda: render_solicitudes_tutor() if tabview.get() == "Solicitudes de Alumnos" else render_mis_tutorias())
        render_solicitudes_tutor()

if __name__ == "__main__":
    app = AppTutoriasPersistente()
    app.mainloop()
# ansible-audit-callback-plugin
# 🛡️ Ansible Audit Callback Plugin: Registro y Auditoría de Comandos (audit_commands)

Este es un *callback plugin* avanzado para Ansible diseñado para registrar de forma detallada las acciones ejecutadas durante la automatización. Su objetivo principal es fortalecer la **auditoría** y el **cumplimiento (compliance)** en entornos críticos al garantizar que cada cambio y su contexto sean registrados tanto en el servidor controlador como en la máquina remota.

---

## ✨ Características Principales

* **Registro Centralizado y Distribuido:** Los logs se guardan localmente en el servidor controlador (`ANSIBLE_LOG_DIR`) y son inmediatamente replicados en el host remoto (`/var/log/ansible_audit`).
* **Formato JSON Detallado:** La salida está normalizada en formato JSON, facilitando la integración con herramientas de Log Management (ELK Stack, Splunk, etc.).
* **Integridad de la Auditoría:** Registra el **usuario que ejecuta** (`executor`), el **módulo**, los **argumentos** y el estado de `changed`.
* **Control de Versiones del Estado (Diff):** Captura las salidas `output_before` y `output_after` si la tarea proporciona información de `diff` (ej. con los módulos `template` o `copy`).
* **Omisión Inteligente:** Descarta las tareas de bajo valor como `gather_facts` y `setup` para mantener el log limpio y enfocado en los cambios reales.
* **Seguridad:** Aplica permisos estrictos (`0o600` / `700`) a los archivos y directorios de log para restringir el acceso.

## 🛠️ Requisitos

* Ansible 2.9 o superior.
* Python 3.x.
* El usuario de ejecución debe tener permisos para crear directorios y ejecutar comandos en el host remoto (generalmente a través de `sudo`).

## 🚀 Instalación y Uso

### A. Ubicación del Plugin

Coloca el archivo `audit_commands.py` en uno de los siguientes directorios:

1.  **Directorio de la Ejecución:** En una carpeta llamada `callback_plugins` dentro de tu proyecto.
2.  **Global (Recomendado para producción):** Copia el archivo a `/etc/ansible/callback_plugins/`.

### B. Configuración de Entorno

Asegúrate de configurar la variable de entorno para la ubicación local de los logs:


# Exportar la variable antes de ejecutar el playbook
export ANSIBLE_LOG_DIR="/ruta/al/log/local/ansible"

C. Ejecución

Simplemente ejecuta tu playbook de forma normal. El plugin se activará automáticamente al inicio de la ejecución.

ansible-playbook -i inventory/prod my_auditoria_playbook.yml

⚙️ Estructura del Log (JSON)
Cada línea del archivo de log es un objeto JSON que contendrá campos como:

JSON

{
    "timestamp": "2025-11-19 19:00:00",
    "host": {"name": "server_db_01"},
    "groups": ["databases", "prod"],
    "executor": "adil.ait",
    "task": {
        "name": "Aplicar Configuración de NTP",
        "action": "ansible.builtin.copy",
        "args": {"src": "ntp.conf", "dest": "/etc/ntp.conf"}
    },
    "status": "ok",
    "changed": true,
    "output_before": "contenido_antiguo_del_archivo...",
    "output_after": "contenido_nuevo_del_archivo..."
}
🙋‍♂️ Contribuciones y Contacto
Este proyecto es de código abierto. ¡Las contribuciones son bienvenidas!

Problemas/Bugs: Por favor, abre un [Issue] en este repositorio.

Contacto: Mi Perfil de LinkedIn

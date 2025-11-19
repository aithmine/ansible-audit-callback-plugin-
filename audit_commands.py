#
#
# Callback Plugin de Ansible para Auditoría de Logs
# @adil.ait
# --------------------------------------------------
# Mejoras realizadas:
#
# **Incorporación de la variable ANSIBLE_LOG_DIR.
# **Creación de directorio para los /var/log/ansible_audit.
# **Incorporación de la información de ejecución del usuario (executor_user)**: Se añade el nombre del usuario que ejecuta la tarea.
# **Normalización de las salidas de `output_before` y `output_after`**: Se almacena la información antes y después de la tarea cuando está disponible.
# **Generación de Logs en formato JSON**: Se guardan los logs en un formato JSON detallado.
# **Envío de logs a todas las máquinas remotas**: Después de guardar localmente
# **Mejora en la organización del código**: Se separaron funciones de procesamiento de tareas, almacenamiento local y envío remoto.
# **Descartar tareas "gather_facts" y "setup"**: Se omiten las tareas que corresponden a "gather_facts" y "setup" para evitar sobrecargar el log.
# **Tratamiento de campos nulos (null)**: Las salidas `output_before` y `output_after` ahora se manejan para ser `null` si no hay datos.
# **Extracción de información de IP**: Se obtiene la primera dirección IPv4 disponible del host.

import os
import json
import subprocess
from datetime import datetime
from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """
    Callback plugin para registrar logs y copiarlos a todas las máquinas remotas.
    Ignora las tareas gather_facts y setup.
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'audit_log_to_remote'

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.logs = []
        self.log_dir = os.getenv('ANSIBLE_LOG_DIR')
        if not self.log_dir:
            self._display.warning("La variable de entorno ANSIBLE_LOG_DIR no está configurada, usando '/var/log/ansible_audit' por defecto.")
            self.log_dir = '/var/log/ansible_audit'

        self.execution_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Crear el directorio si no existe
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except OSError as e:
            self._display.warning(f"Error al crear el directorio de logs: {e}")

    def _process_task(self, result, status):
        """
        Procesa la información de una tarea y genera el log correspondiente.
        """
        # Filtrar tarea de gather_facts y setup
        if result._task.action == "gather_facts" or result._task.action == "setup":
            self._display.vvv(f"Ignorando tarea '{result._task.action}'")
            return  # No procesamos esta tarea

        host = result._host.get_name()
        task_name = result.task_name
        task_action = result._task.action
        task_args = result._task.args
        changed = result._result.get('changed', False)

        # Normalizamos campos vacíos
        output_before = result._result.get('diff', {}).get('before', None)
        if isinstance(output_before, str) and output_before == "":
            output_before = None  # Si es un string vacío, lo tratamos como None

        output_after = result._result.get('diff', {}).get('after', None)
        if isinstance(output_after, str) and output_after == "":
            output_after = None  # Similar para 'after'

        host_vars = result._host.get_vars()
        host_ip = host_vars.get('ansible_host', 'Unknown')
        host_groups = host_vars.get('group_names', [])
        os_type = host_vars.get('ansible_distribution', 'Unknown')
        executor_user = os.getenv('USER', 'unknown')

        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        log_entry = {
            "timestamp": start_time,
            "host": {"name": host},
            "groups": host_groups,
            "executor": executor_user,
            "task": {"name": task_name, "action": task_action, "args": task_args},
            "status": status,
            "changed": changed,
            "output_before": output_before,  # Aquí usaremos output_before ya normalizado
            "output_after": output_after   # Y output_after también normalizado
        }

        self._save_log_local(host, log_entry)
        self._send_log_to_remote(host)

    def v2_runner_on_ok(self, result):
        """
        Procesar resultado exitoso de una tarea.
        """
        self._process_task(result, "ok")

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """
        Procesar resultado fallido de una tarea.
        """
        self._process_task(result, "failed")

    def _save_log_local(self, host, log_entry):
        """
        Guardar el log localmente en el servidor controlador.
        """
        log_file_name = f"{host}_{self.execution_timestamp}.json"
        log_file_path = os.path.join(self.log_dir, log_file_name)

        try:
            with open(log_file_path, "a") as log_file:
                json.dump(log_entry, log_file)
                log_file.write("\n")
            os.chmod(log_file_path, 0o600)
        except IOError as e:
            self._display.warning(f"Error al guardar el log localmente: {e}")

    def _send_log_to_remote(self, host):
        """
        Crear el directorio remoto y enviar el log a todas las máquinas remotas en /var/log/ansible_audit.
        """
        log_file_name = f"{host}_{self.execution_timestamp}.json"
        log_file_path = os.path.join(self.log_dir, log_file_name)
        dest_path = f"/var/log/ansible_audit/{log_file_name}"

        try:
            # Crear el directorio en la máquina remota si no existe
            subprocess.run(
                ["ansible", host, "-m", "shell", "-a", "mkdir -p /var/log/ansible_audit && chmod 700 /var/log/ansible_audit"],
                capture_output=True,
                text=True,
                check=True
            )

            # Copiar el archivo de log al directorio remoto
            result = subprocess.run(
                ["ansible", host, "-m", "copy", "-a", f"src={log_file_path} dest={dest_path} mode=0600"],
                capture_output=True,
                text=True,
                check=True
            )
            self._display.vvv(f"Log enviado a {host}: {result.stdout}")
        except subprocess.CalledProcessError as e:
            self._display.warning(f"Error al enviar el log al host remoto {host}: {e.stderr}")


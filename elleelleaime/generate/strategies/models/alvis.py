from generate.strategies.strategy import PatchGenerationStrategy
from dotenv import load_dotenv
from typing import Any

import os
import uuid
import paramiko
import json

class AlvisHFModels(PatchGenerationStrategy):
    
    def __init__(self, model: str) -> None:
        self.model = model
        load_dotenv()
        self.hostname = os.getenv("ALVIS_HOSTNAME") or "alvis"
        self.username = os.getenv("ALVIS_USERNAME")
        self.password = os.getenv("ALVIS_PASSWORD")

    
    def _generate_impl(self, prompt: str) -> Any:
        # Generate unique id
        unique_id = str(uuid.uuid4())

        # Connect to remote cluster using paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=self.hostname, username=self.username, password=self.password)

        # Create scripts and test data on the remote cluster
        self._create_scripts(ssh, prompt, unique_id)

        # Submit job to Slurm on the remote cluster and wait for its conclusion
        self._submit_job(ssh, unique_id)

        # Retrieve the results
        results = self._retrieve_results(ssh, unique_id)

        # Close the SSH connection
        ssh.close()

        return results
    
    
    def _create_scripts(self, ssh, prompt, unique_id):
        # Write the test samples file to a file on the remote cluster
        # FIXME remove hard-coded paths (maybe go for /tmp/)
        with ssh.open_sftp() as sftp:
            with sftp.open(f"/cephyr/users/{self.username}/Alvis/elleelleaime/jobs/{unique_id}_inputs.txt", "w+") as f:
                f.write(prompt)

        # Write the HuggingFace script to a file on the remote cluster
        # FIXME remove hard-coded paths (maybe go for /tmp/)
        # FIXME: get parameters from cli
        with ssh.open_sftp() as sftp:
            with sftp.open(f"/cephyr/users/{self.username}/Alvis/elleelleaime/jobs/{unique_id}_inference.py", "w+") as f:
                with open('./resources/scripts/inference.py', 'r') as lf:
                    script = lf.read().format(model=self.model,
                                              max_new_tokens=512,
                                              num_return_sequences=10,
                                              unique_id=unique_id)
                    f.write(script)
                    
        # Write the jobscript to a file on the remote cluster
        # FIXME remove hard-coded paths (maybe go for /tmp/)
        # FIXME: get parameters from cli
        with ssh.open_sftp() as sftp:
            with sftp.open(f'/cephyr/users/{self.username}/Alvis/elleelleaime/jobs/{unique_id}_jobscript', 'w+') as f:
                with open('./resources/scripts/jobscript', 'r') as lf:
                    script = lf.read().format(job_name="elleelleaime",
                                              gpu_type="A40",
                                              gpu_number="1",
                                              job_time="00:10:00",
                                              script=f"/cephyr/users/{self.username}/Alvis/elleelleaime/jobs/{unique_id}_inference.py")
                    f.write(script)


    def _submit_job(self, ssh, unique_id):
        # Submit job to Slurm
        # FIXME remove hard-coded paths (maybe go for /tmp/)
        # FIXME setup_env.sh should also be written by elleelleaime
        command = f'cd elleelleaime && source setup_env.sh && cd jobs && sbatch --wait {unique_id}_jobscript && wait'
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.recv_exit_status()
        stderr.channel.recv_exit_status()
        print(stdout.readlines())
        print(stderr.readlines())


    def _retrieve_results(self, ssh, unique_id):
        # Retrieve the results from the remote cluster
        # FIXME remove hard-coded paths (maybe go for /tmp/)
        # FIXME setup_env.sh should also be written by elleelleaime
        with ssh.open_sftp() as sftp:
            sftp.get(f'/cephyr/users/{self.username}/Alvis/elleelleaime/jobs/{unique_id}_predictions.txt', f'{unique_id}_predictions.txt')

        # Read the output file and return the results as a string
        with open(f'{unique_id}_predictions.txt', 'r') as f:
            results = json.loads(f.read())
            
        # Remove the output file

        return results

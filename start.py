import subprocess
script_path = "alert.py"

# Start the script in the background
subprocess.Popen(["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print("Alert.py started")

subprocess.run("python -m gunicorn -w 1 -b 0.0.0.0:1234 tracker:app --log-level=debug --log-file=files/web.log", shell=True)
print("Web server started")
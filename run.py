from flask import Response, render_template,make_response, redirect, url_for, request
import cv2
from app import app, camera

recording = True


# Fonction pour capturer la vidéo en temps réel
def generate_frames():
    while recording:  # Continuer à capturer et diffuser tant que l'enregistrement est activé
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                

# Page de connexion
@app.route('/login')
def login():
    return render_template('login.html')


# Page de deconnexion
@app.route('/logout')
def logout():
    resp = make_response(render_template('login.html'))
    resp.delete_cookie('utilisateur_camera')
    return resp


@app.route('/video')
def video():
    global recording
    if recording:
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    return redirect(url_for('stop_recording'))

@app.route('/stop_recording', methods=['GET'])
def stop_recording():
    global recording
    if request.cookies.get('utilisateur_camera') != "drissa":
        return redirect(url_for('login'))
    recording = False
    return render_template("stopped.html", recording=recording)

@app.route('/pre_stop_recording', methods=['GET'])
def pre_stop_recording():
    global recording
    recording = True
    return redirect(url_for('home'))

@app.route('/', methods=['POST', 'GET'])
def home():
    global recording
    utilisateur = request.cookies.get('utilisateur_camera')
    if request.method == 'POST':
        if request.form.get('username') == "drissa" and request.form.get('password') == "ancien123":
            if not recording:
                resp = make_response(render_template('stopped.html', utilisateur=request.form.get('username')))
                resp.set_cookie('utilisateur_camera', request.form.get('username'), max_age=2592000)
                return resp
            resp = make_response(render_template('video.html', utilisateur=request.form.get('username')))
            resp.set_cookie('utilisateur_camera', request.form.get('username'), max_age=2592000)
            return resp
        else:
            return redirect(url_for('home'))
    if utilisateur:
        if not recording:
            return render_template('stopped.html', utilisateur=utilisateur)
        return render_template('video.html', utilisateur=utilisateur)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
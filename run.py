from flask import Response, render_template,make_response, redirect, url_for, request
import cv2
from app import *
from datetime import datetime
import os

saved = False
static_folder = "app/static/"

# Fonction pour capturer la vidéo en temps réel
def generate_frames():
    global recording, result
    while recording:  # Continuer à capturer et diffuser tant que l'enregistrement est activé
        if datetime.now().minute == 18:
            recording = False
        success, frame = camera.read()
        if not success:
            break
        else:
            #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.flip(frame, 1)
            frame = cv2.putText(frame ,str(datetime.now()), (0, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1, cv2.LINE_4)
            
            # Write the frame into the
            # file 'filename.avi'
            result.write(frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            if not recording:
                result.release()
            if ret:
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                
def initVideoContainer():
    global filename, result
    filename = "_".join(
                "_".join(
                    "_".join("_".join(str(datetime.now()).split(" ")).split(":")).split("-")
                ).split(".")
            )
    result = cv2.VideoWriter(
                f"{tmp_dir}{filename}.avi", cv2.VideoWriter_fourcc(*"MJPG"), 15, size
            )
    
def getVideoThumbnail(filename):
    global tmp_dir
    cap = cv2.VideoCapture(f"{tmp_dir}{filename}.avi")
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(f"app/{static_folder}'thumbnails/'{filename}.png", frame)
    else:
        print("Error: can't create thumbnail")
    cap.release()


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
    global recording, filename, result, camera
    if recording:
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    return redirect(url_for('stop_recording'))

@app.route('/stop_recording', methods=['GET'])
def stop_recording():
    global recording, result
    if request.cookies.get('utilisateur_camera') != "drissa":
        return redirect(url_for('login'))
    recording = False
    camera.release()
    return render_template("stopped.html", recording=recording)

@app.route('/pre_stop_recording', methods=['GET'])
def pre_stop_recording():
    global recording, camera
    recording = True
    camera = cv2.VideoCapture(0)
    return redirect(url_for('home'))

@app.route('/save_recording', methods=['GET'])
def save_recording():
    global recording, filename, result
    result.release()
    getVideoThumbnail(filename)
    return render_template("saved.html", filename=filename)

@app.route('/video_listing', methods=['GET'])
def video_listing():
    video_folder = f'{video_folder}/videos'
    for video in os.listdir(video_folder):
        if video.endswith(('.avi')):
            getVideoThumbnail(os.path.splitext(video)[0])
    videos = [video for video in os.listdir(video_folder) if video.endswith(('.avi'))]
    video_paths = [f'{video_folder}/{video}' for video in videos]

    # Vous pouvez utiliser des miniatures des vidéos à l'aide de bibliothèques comme ffmpeg-thumbnailer
    # Assurez-vous d'installer ffmpeg-thumbnailer en utilisant la commande : sudo apt-get install ffmpeg-thumbnailer
    thumbnails = [f'{video_folder}/thumbnails/{os.path.splitext(video)[0]}.png' for video in videos]

    return render_template('video_listing.html', videos=zip(videos, video_paths, thumbnails))

@app.route('/', methods=['POST', 'GET'])
def home():
    global recording, camera, result
    utilisateur = request.cookies.get('utilisateur_camera')
    if request.method == 'POST':
        if request.form.get('username') == "drissa" and request.form.get('password') == "ancien123":
            if not recording:
                resp = make_response(render_template('stopped.html', utilisateur=request.form.get('username')))
                resp.set_cookie('utilisateur_camera', request.form.get('username'), max_age=2592000)
                return resp
            initVideoContainer()
            resp = make_response(render_template('video.html', utilisateur=request.form.get('username')))
            resp.set_cookie('utilisateur_camera', request.form.get('username'), max_age=2592000)
            return resp
        else:
            return redirect(url_for('home'))
    initVideoContainer()
    if not recording:
        camera = cv2.VideoCapture(0)
    if request.args.get("user") == "computer":
        return render_template('video.html', utilisateur="drissa")
    if utilisateur:
        if not recording:
            return render_template('stopped.html', utilisateur=utilisateur)
        return render_template('video.html', utilisateur=utilisateur)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
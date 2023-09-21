import datetime
from Blog import models
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from Blog import Notification  


app = Flask(__name__)
app.config['SECRET_KEY'] = 'xoxo'  # Cambia esto por una clave segura
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'  # SQLite para la base de datos

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Definir el modelo de usuario
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    date_of_birth = db.Column(db.Date)
    # Agrega otros campos según sea necesario para el perfil del usuario


# Modelo para las publicaciones en el blog
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref='posts')
    tags = db.Column(db.String(100))  # Campo para etiquetas o palabras clave

# Agrega un modelo para los comentarios
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    post = db.relationship('Post', backref='comments')
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref='comments')

    class Notification(db.Model):
        id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='notifications')
    message = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user, message):
        self.user = user
        self.message = message

# Código para crear una nueva publicación
new_post = Post(title="Título de la publicación", content="Contenido de la publicación", author=current_user)
db.session.add(new_post)
db.session.commit()

# Generar una notificación para los seguidores del usuario actual
followers = current_user.followers.all()
for follower in followers:
    notification = Notification(user=follower, message=f'Nueva publicación de {current_user.username}: {new_post.title}')
    db.session.add(notification)
db.session.commit()



# Ruta para agregar una nueva publicación
@app.route('/agregar_publicacion', methods=['GET', 'POST'])
@login_required
def agregar_publicacion():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_post = Post(title=title, content=content, author=current_user)
        db.session.add(new_post)
        db.session.commit()
        flash('Publicación agregada exitosamente', 'success')
        return redirect(url_for('dashboard'))
    return render_template('agregar_publicacion.html')

# Ruta para editar una publicación existente
@app.route('/editar_publicacion/<int:post_id>', methods=['GET', 'POST'])
@login_required
def editar_publicacion(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        flash('Publicación actualizada exitosamente', 'success')
        return redirect(url_for('dashboard'))
    return render_template('editar_publicacion.html', post=post)

# Ruta para eliminar una publicación existente
@app.route('/eliminar_publicacion/<int:post_id>', methods=['POST'])
@login_required
def eliminar_publicacion(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        return redirect(url_for('dashboard'))
    db.session.delete(post)
    db.session.commit()
    flash('Publicación eliminada exitosamente', 'success')
    return redirect(url_for('dashboard'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # Esto es solo un ejemplo básico, NO es seguro
            login_user(user)
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas. Intenta nuevamente.', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Aquí puedes mostrar las publicaciones del usuario autenticado
    posts = Post.query.filter_by(author=current_user).all()
    return render_template('dashboard.html', posts=posts)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Ruta para registrar un nuevo usuario
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            flash('El nombre de usuario ya está en uso. Elige otro.', 'danger')
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registro exitoso. Inicia sesión para comenzar.', 'success')
            return redirect(url_for('login'))
    return render_template('registro.html')

@app.route('/buscar', methods=['GET', 'POST'])
def buscar():
    if request.method == 'POST':
        keyword = request.form['keyword']
        # Realiza una búsqueda en la base de datos por título, contenido o etiquetas
        posts = Post.query.filter(
            (Post.title.contains(keyword)) |
            (Post.content.contains(keyword)) |
            (Post.tags.contains(keyword))
        ).all()
        return render_template('resultados_busqueda.html', posts=posts, keyword=keyword)
    return render_template('buscar.html')

@app.route('/filtrar', methods=['GET', 'POST'])
def filtrar():
    if request.method == 'POST':
        # Obtener los criterios de filtro desde el formulario
        categoria = request.form.get('categoria')
        fecha = request.form.get('fecha')

        # Realizar la consulta de filtrado en la base de datos
        filtered_posts = Post.query.filter_by(categoria=categoria, fecha=fecha).all()
        
        return render_template('resultados_filtrados.html', posts=filtered_posts, categoria=categoria, fecha=fecha)
    
    return render_template('filtrar.html')

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        # Aquí procesa la solicitud de edición del perfil y actualiza la información en la base de datos
        current_user.name = request.form['name']
        current_user.email = request.form['email']
        current_user.date_of_birth = request.form['date_of_birth']
        # Agrega más campos según sea necesario
        
        db.session.commit()
        flash('Perfil actualizado exitosamente', 'success')
        return redirect(url_for('perfil'))
    
    return render_template('perfil.html')

@app.route('/notificaciones')
@login_required
def notificaciones():
    user_notifications = current_user.notifications.order_by(Notification.timestamp.desc()).all()
    return render_template('notificaciones.html', notifications=user_notifications)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)

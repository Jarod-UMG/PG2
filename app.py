from flask import Flask, render_template, request, session, flash, redirect, url_for, Response
from flask_wtf import FlaskForm
from wtforms import HiddenField
from flask_paginate import Pagination, get_page_args
from flask_bootstrap import Bootstrap
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import cx_Oracle
import os
import time
import requests

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'admin'

dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
connection = cx_Oracle.connect(user='USR_FERRETERIA', password='admin', dsn=dsn)


class DeleteForm(FlaskForm):
    _method = HiddenField()


@app.route('/')  # Ruta para la página index
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])  # Ruta para iniciar sesión
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        cursor = connection.cursor()
        cursor.execute("SELECT ID_ROL, NOMBRE FROM USUARIOS WHERE CORREO = :correo AND CONTRASENA = :contrasena", {
                       'correo': correo, 'contrasena': contrasena})
        user = cursor.fetchone()
        if user:
            id_rol_u = user[0]
            nombre_rol_u = user[1]
            print("id_rol:", id_rol_u)
            if id_rol_u == 1:
                session['id_rol'] = id_rol_u
                session['nombre'] = nombre_rol_u
                return redirect(url_for('dashboard'))
        else:
            session['mensaje'] = 'Contraseña/Correo incorrectos o campos vacios, vuelva a intentar por favor!!!'

    return render_template('login.html')

@app.route('/logout') # ruta para cerrar sesión
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')  # Ruta para la página de adminstrador
def dashboard():
    if 'id_rol' in session:
        id_rol_u = session['id_rol']
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))

@app.route('/admin/products')  # Ruta para la página de productos
def products():
    cursor = connection.cursor()
    cursor.execute("SELECT P.ID_PRODUCTO, P.NOMBRE_PRODUCTO, P.DESCRIPCION, C.NOMBRE_CATEGORIA, M.NOMBRE_MARCA, P.PRECIO, P.EXISTENCIA, P.IMAGEN, P.COSTE FROM PRODUCTOS P JOIN CATEGORIAS C ON P.ID_CATEGORIA = C.ID_CATEGORIA JOIN MARCAS M ON P.ID_MARCA = M.ID_MARCA ORDER BY P.ID_PRODUCTO DESC")
    productos = cursor.fetchall()
    cursor.close()

    cursor2 = connection.cursor()
    cursor2.execute("SELECT ID_CATEGORIA, NOMBRE_CATEGORIA FROM CATEGORIAS")
    categoriasproductos = cursor2.fetchall()
    cursor2.close()

    cursor3 = connection.cursor()
    cursor3.execute("SELECT ID_MARCA, NOMBRE_MARCA FROM MARCAS")
    marcasproductos = cursor3.fetchall()
    cursor3.close()

    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=16)
    total_products = len(productos)
    start = (page - 1) * per_page
    end = start + per_page
    products_to_display = productos[start:end]
    pagination = Pagination(page=page, per_page=per_page, total=total_products,
                            css_framework='bootstrap4', display_msg='{start} - {end} / {total}')

    if 'id_rol' in session:
        id_rol_u = session['id_rol']
        return render_template('products.html', productos=products_to_display, categoriasproductos=categoriasproductos, marcasproductos=marcasproductos, pagination=pagination)
    else:
        return redirect(url_for('login'))

@app.route('/newProducts')
def newProducts():
    cursor2 = connection.cursor()
    cursor2.execute("SELECT ID_CATEGORIA, NOMBRE_CATEGORIA FROM CATEGORIAS")
    categoriasproductos = cursor2.fetchall()
    cursor2.close()

    cursor3 = connection.cursor()
    cursor3.execute("SELECT ID_MARCA, NOMBRE_MARCA FROM MARCAS")
    marcasproductos = cursor3.fetchall()
    cursor3.close()

    if 'id_rol' in session:
        id_rol = session['id_rol']
        return render_template('newProducts.html', categoriasproductos=categoriasproductos, marcasproductos=marcasproductos)
    else:
        return redirect(url_for('login'))

@app.route('/crear_producto', methods=['POST']) # Ruta para crear a Oracle los datos del producto
def crear_producto():
    nombre_producto = request.form.get('nombre_producto')
    descripcion = request.form.get('descripcion')
    id_categoria = request.form.get('id_categoria')
    id_marca = request.form.get('id_marca')
    precio = request.form.get('precio')
    existencia = request.form.get('existencia')
    imagen = request.files['imagen']
    coste = request.form.get('coste')

    if imagen:
        imagen.save(os.path.join('static/imgbd', imagen.filename))
        ruta_imagen = os.path.join('imgbd/', imagen.filename)
    else:
        ruta_imagen = os.path.join('imgbd/no producto.jpg')

    sql = "INSERT INTO productos (nombre_producto, descripcion, id_categoria, id_marca, precio, existencia, imagen, coste) VALUES (:nombre_producto, :descripcion, :id_categoria, :id_marca, :precio, :existencia, :imagen, :coste)"

    cursor = connection.cursor()
    cursor.execute(sql, {'nombre_producto': nombre_producto, 'descripcion': descripcion, 'id_categoria': id_categoria,
                   'id_marca': id_marca, 'precio': precio, 'existencia': existencia, 'imagen': ruta_imagen, 'coste': coste})
    connection.commit()

    if 'id_rol' in session:
        id_rol = session['id_rol']
        return redirect(url_for('newProducts'))
    else:
        return redirect(url_for('login'))

@app.route('/editProducts/<int:ID_PRODUCTO>', methods=['GET', 'POST']) # ruta para editar productos
def editProducts(ID_PRODUCTO):
    if request.method == 'GET':
        try:
            dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
            connection = cx_Oracle.connect(user='USR_FERRETERIA', password='admin', dsn=dsn)
            cursor = connection.cursor()
            query = "SELECT ID_PRODUCTO, nombre_producto, descripcion, id_categoria, id_marca, precio, existencia, imagen, coste FROM productos WHERE ID_PRODUCTO = :id_producto"
            cursor.execute(query, id_producto=ID_PRODUCTO)
            producto = cursor.fetchone()
            cursor.close()

            cursor2 = connection.cursor()
            cursor2.execute("SELECT ID_CATEGORIA, NOMBRE_CATEGORIA FROM CATEGORIAS")
            categoriasproductos = cursor2.fetchall()
            cursor2.close()

            cursor3 = connection.cursor()
            cursor3.execute("SELECT ID_MARCA, NOMBRE_MARCA FROM MARCAS")
            marcasproductos = cursor3.fetchall()
            cursor3.close()
            connection.close()

            if producto is None:
                return redirect(url_for('products'))

            if 'id_rol' in session:
                id_rol_u = session['id_rol']
                return render_template('editProducts.html', producto=producto, categoriasproductos=categoriasproductos, marcasproductos=marcasproductos)
            else:
                return redirect(url_for('login'))

        except Exception as e:
            print("Error al obtener el producto:", str(e))
            return redirect(url_for('products'))

    elif request.method == 'POST':
        try:
            dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
            connection = cx_Oracle.connect(user='USR_FERRETERIA', password='admin', dsn=dsn)
            cursor = connection.cursor()

            nombre_producto = request.form.get('nombre_producto')
            descripcion = request.form.get('descripcion')
            id_categoria = request.form.get('id_categoria')
            id_marca = request.form.get('id_marca')
            precio = request.form.get('precio')
            existencia = request.form.get('existencia')
            coste = request.form.get('coste')

            cursor.execute("SELECT imagen FROM productos WHERE ID_PRODUCTO = :id_producto", id_producto=ID_PRODUCTO)
            resultado = cursor.fetchone()
            imagen_actual = resultado[0] if resultado else None

            imagen = request.files.get('imagen')

            if imagen:
                imagen.save(os.path.join('static/imgbd', imagen.filename))
                ruta_imagen = os.path.join('imgbd/', imagen.filename)
            else:
                ruta_imagen = imagen_actual

            query = "UPDATE productos SET nombre_producto = :nombre_producto, descripcion = :descripcion, id_categoria = :id_categoria, id_marca = :id_marca, precio = :precio, existencia = :existencia, imagen = :imagen, coste = :coste WHERE ID_PRODUCTO = :id_producto"

            cursor.execute(query, nombre_producto=nombre_producto, descripcion=descripcion, id_categoria=id_categoria,
                           id_marca=id_marca, precio=precio, existencia=existencia, imagen=ruta_imagen, coste=coste, id_producto=ID_PRODUCTO)
            connection.commit()
            cursor.close()
            connection.close()

            return redirect(url_for('products'))

        except Exception as e:
            print("Error al actualizar el producto:", str(e))
            return redirect(url_for('products'))

@app.route('/eliminar_producto/<int:ID_PRODUCTO>', methods=['POST', 'DELETE']) # ruta para eliminar productos
def eliminar_producto(ID_PRODUCTO):
    if request.method == 'POST' or request.form.get('_method') == 'DELETE':
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM PRODUCTOS WHERE ID_PRODUCTO = :ID_PRODUCTO", {'ID_PRODUCTO': ID_PRODUCTO})
            connection.commit()
            flash('Producto eliminado con éxito', 'success')
        except Exception as e:
            flash('Error al eliminar el producto', 'danger')
        finally:
            cursor.close()

    return redirect(url_for('products'))

@app.route('/buscar_productos', methods=['POST'])  # ruta para buscar productos
def buscar_productos():
    campo_busqueda = request.form.get('campo_busqueda')
    valor_busqueda = request.form.get('valor_busqueda')

    query = "SELECT P.ID_PRODUCTO, P.NOMBRE_PRODUCTO, P.DESCRIPCION, C.NOMBRE_CATEGORIA, M.NOMBRE_MARCA, P.PRECIO, P.EXISTENCIA, P.IMAGEN FROM productos P JOIN CATEGORIAS C ON P.ID_CATEGORIA = C.ID_CATEGORIA JOIN MARCAS M ON P.ID_MARCA = M.ID_MARCA"
    params = {}

    if campo_busqueda == "nombre_producto" and valor_busqueda:
        query += " WHERE 1=1 AND UPPER(nombre_producto) LIKE UPPER(:nombre_producto)"
        params['nombre_producto'] = f'%{valor_busqueda}%'
    elif campo_busqueda == "nombre_categoria" and valor_busqueda:
        query += " WHERE 1=1 AND UPPER(nombre_categoria) LIKE UPPER(:nombre_categoria)"
        params['nombre_categoria'] = f'%{valor_busqueda}%'
    elif campo_busqueda == "nombre_marca" and valor_busqueda:
        query += " WHERE 1=1 AND UPPER(nombre_marca) LIKE UPPER(:nombre_marca)"
        params['nombre_marca'] = f'%{valor_busqueda}%'
    elif (campo_busqueda or valor_busqueda) or (campo_busqueda == "nada" and valor_busqueda):
        query += " ORDER BY P.ID_PRODUCTO DESC"

    cursor = connection.cursor()
    cursor.execute(query, params)
    productos_encontrados = cursor.fetchall()
    cursor.close()

    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=16)
    total_products = len(productos_encontrados)
    start = (page - 1) * per_page
    end = start + per_page
    products_to_display = productos_encontrados[start:end]
    pagination = Pagination(page=page, per_page=per_page, total=total_products,
                            css_framework='bootstrap4', display_msg='{start} - {end} / {total}')

    if 'id_rol' in session:
        id_rol_u = session['id_rol']
        return render_template('resultadosBusquedaProducto.html', productos=productos_encontrados, productos_encontrados=products_to_display, pagination=pagination)
    else:
        return redirect(url_for('login'))

@app.route('/admin/categories')  # ruta para la pagina categorias
def categories():
    cursor = connection.cursor()
    cursor.execute("SELECT ID_CATEGORIA, NOMBRE_CATEGORIA FROM CATEGORIAS ORDER BY ID_CATEGORIA DESC")
    categorias = cursor.fetchall()
    cursor.close()

    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=16)
    total_category = len(categorias)
    start = (page - 1) * per_page
    end = start + per_page
    category_to_display = categorias[start:end]
    pagination = Pagination(page=page, per_page=per_page, total=total_category,
                            css_framework='bootstrap4', display_msg='{start} - {end} / {total}')
    if 'id_rol' in session:
        id_rol_u = session['id_rol']
        return render_template('categories.html', categorias=category_to_display, pagination=pagination)
    else:
        return redirect(url_for('login'))

@app.route('/newCategories')
def newCategories():
    if 'id_rol' in session:
        id_rol = session['id_rol']
        return render_template('newCategories.html')
    else:
        return redirect(url_for('login'))

@app.route('/crear_categoria', methods=['POST']) # Ruta para crear a Oracle los datos de categoría
def crear_categoria():
    nombre_categoria = request.form.get('nombre_categoria')

    sql = "INSERT INTO categorias (nombre_categoria) VALUES (:nombre_categoria)"

    cursor = connection.cursor()
    cursor.execute(sql, {'nombre_categoria': nombre_categoria})
    connection.commit()

    return redirect(url_for('categories'))

@app.route('/editCategories/<int:ID_CATEGORIA>', methods=['GET', 'POST']) # ruta para editar categoria
def editCategories(ID_CATEGORIA):
    if request.method == 'GET':
        try:
            dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
            connection = cx_Oracle.connect(user='USR_FERRETERIA', password='admin', dsn=dsn)
            cursor = connection.cursor()
            query = "SELECT ID_CATEGORIA, nombre_categoria FROM categorias WHERE ID_CATEGORIA = :id_categoria"
            cursor.execute(query, id_categoria=ID_CATEGORIA)
            categoria = cursor.fetchone()
            cursor.close()
            connection.close()

            if categoria is None:
                return redirect(url_for('categories'))

            if 'id_rol' in session:
                id_rol_u = session['id_rol']
                return render_template('editCategories.html', categoria=categoria)
            else:
                return redirect(url_for('login'))

        except Exception as e:
            print("Error al obtener la categoria:", str(e))
            return redirect(url_for('categories'))

    elif request.method == 'POST':
        try:
            dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
            connection = cx_Oracle.connect(user='USR_FERRETERIA', password='admin', dsn=dsn)

            cursor = connection.cursor()
            nombre_categoria = request.form.get('nombre_categoria')
            query = "UPDATE categorias SET nombre_categoria = :nombre_categoria WHERE ID_CATEGORIA = :id_categoria"
            cursor.execute(query, nombre_categoria=nombre_categoria,id_categoria=ID_CATEGORIA)
            connection.commit()
            cursor.close()
            connection.close()

            return redirect(url_for('categories'))

        except Exception as e:
            print("Error al actualizar la categoria:", str(e))
            return redirect(url_for('categories'))

@app.route('/eliminar_categoria/<int:ID_CATEGORIA>', methods=['POST', 'DELETE']) # ruta para eliminar categoria
def eliminar_categoria(ID_CATEGORIA):
    if request.method == 'POST' or request.form.get('_method') == 'DELETE':
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM CATEGORIAS WHERE ID_CATEGORIA = :ID_CATEGORIA", {'ID_CATEGORIA': ID_CATEGORIA})
            connection.commit()
            flash('Categoria eliminada con éxito', 'success')
        except Exception as e:
            flash('Error al eliminar la categoria', 'danger')
        finally:
            cursor.close()

    return redirect(url_for('categories'))

@app.route('/buscar_categorias', methods=['POST'])  # ruta para buscar categorias
def buscar_categorias():
    campo_busqueda = request.form.get('campo_busqueda')
    valor_busqueda = request.form.get('valor_busqueda')

    query = "SELECT C.ID_CATEGORIA, C.NOMBRE_CATEGORIA FROM CATEGORIAS C"
    params = {}

    if campo_busqueda == "nombre_categoria" and valor_busqueda:
        query += " WHERE 1=1 AND UPPER(nombre_categoria) LIKE UPPER(:nombre_categoria)"
        params['nombre_categoria'] = f'%{valor_busqueda}%'
    elif (campo_busqueda or valor_busqueda) or (campo_busqueda == "nada" and valor_busqueda):
        query += " ORDER BY C.ID_CATEGORIA DESC"

    cursor = connection.cursor()
    cursor.execute(query, params)
    categorias_encontrados = cursor.fetchall()
    cursor.close()

    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=16)
    total_products = len(categorias_encontrados)
    start = (page - 1) * per_page
    end = start + per_page
    categories_to_display = categorias_encontrados[start:end]
    pagination = Pagination(page=page, per_page=per_page, total=total_products,
                            css_framework='bootstrap4', display_msg='{start} - {end} / {total}')

    if 'id_rol' in session:
        id_rol_u = session['id_rol']
        return render_template('resultadosBusquedaCategoria.html', categorias=categorias_encontrados, categorias_encontrados=categories_to_display, pagination=pagination)
    else:
        return redirect(url_for('login'))

@app.route('/admin/brands')  # ruta para la página de marcas
def brands():
    cursor = connection.cursor()
    cursor.execute("SELECT ID_MARCA, NOMBRE_MARCA FROM MARCAS ORDER BY ID_MARCA DESC")
    marcas = cursor.fetchall()
    cursor.close()

    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=16)
    total_brands = len(marcas)
    start = (page - 1) * per_page
    end = start + per_page
    brandas_to_display = marcas[start:end]
    pagination = Pagination(page=page, per_page=per_page, total=total_brands,
                            css_framework='bootstrap4', display_msg='{start} - {end} / {total}')
    if 'id_rol' in session:
        id_rol_u = session['id_rol']
        return render_template('brands.html', marcas=brandas_to_display, pagination=pagination)
    else:
        return redirect(url_for('login'))

@app.route('/newBrands')
def newBrands():
    if 'id_rol' in session:
        id_rol = session['id_rol']
        return render_template('newBrands.html')
    else:
        return redirect(url_for('login'))

@app.route('/crear_marca', methods=['POST']) # Ruta para crear a Oracle los datos de marcas
def crear_marca():
    nombre_marca = request.form.get('nombre_marca')

    # Preparar la consulta SQL
    sql = "INSERT INTO marcas (nombre_marca) VALUES (:nombre_marca)"

    # Ejecutar la consulta
    cursor = connection.cursor()
    cursor.execute(sql, {'nombre_marca': nombre_marca})
    connection.commit()

    # variable de sesion
    session['mensaje'] = 'Marca agregada correctamente'

    return redirect(url_for('brands'))

@app.route('/editBrands/<int:ID_MARCA>', methods=['GET', 'POST']) # ruta para editar marcas
def editBrands(ID_MARCA):
    if request.method == 'GET':
        try:
            dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
            connection = cx_Oracle.connect(user='USR_FERRETERIA', password='admin', dsn=dsn)

            cursor = connection.cursor()
            query = "SELECT ID_MARCA, nombre_marca FROM marcas WHERE ID_MARCA = :id_marca"
            cursor.execute(query, id_marca=ID_MARCA)
            marca = cursor.fetchone()
            cursor.close()
            connection.close()

            if marca is None:
                flash('Marca no encontrada', 'danger')
                return redirect(url_for('brands'))
            if 'id_rol' in session:
                id_rol_u = session['id_rol']
                return render_template('editBrands.html', marca=marca)
            else:
                return redirect(url_for('login'))

        except Exception as e:
            print("Error al obtener la marca:", str(e))
            flash('Error al obtener la marca', 'danger')
            return redirect(url_for('brands'))

    elif request.method == 'POST':
        try:
            dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
            connection = cx_Oracle.connect(user='USR_FERRETERIA', password='admin', dsn=dsn)

            cursor = connection.cursor()
            nombre_marca = request.form.get('nombre_marca')
            query = "UPDATE marcas SET nombre_marca = :nombre_marca WHERE ID_MARCA = :id_marca"
            cursor.execute(query, nombre_marca=nombre_marca, id_marca=ID_MARCA)
            connection.commit()
            cursor.close()
            connection.close()

            flash('Categoria actualizada con éxito', 'success')
            return redirect(url_for('brands'))

        except Exception as e:
            print("Error al actualizar la marca:", str(e))
            flash('Error al actualizar la marca', 'danger')
            return redirect(url_for('brands'))

@app.route('/eliminar_marca/<int:ID_MARCA>', methods=['POST', 'DELETE']) # ruta para eliminar marcas
def eliminar_marca(ID_MARCA):
    if request.method == 'POST' or request.form.get('_method') == 'DELETE':
        # Lógica para eliminar de la base de datos Oracle
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM MARCAS WHERE ID_MARCA = :ID_MARCA", {
                           'ID_MARCA': ID_MARCA})
            connection.commit()
            flash('Marca eliminada con éxito', 'success')
        except Exception as e:
            flash('Error al eliminar la marca', 'danger')
        finally:
            cursor.close()

    return redirect(url_for('brands'))

@app.route('/buscar_marcas', methods=['POST'])  # ruta para buscar marcas
def buscar_marcas():
    campo_busqueda = request.form.get('campo_busqueda')
    valor_busqueda = request.form.get('valor_busqueda')

    query = "SELECT M.ID_MARCA, M.NOMBRE_MARCA FROM MARCAS M"
    params = {}

    if campo_busqueda == "nombre_marca" and valor_busqueda:
        query += " WHERE 1=1 AND UPPER(nombre_marca) LIKE UPPER(:nombre_marca)"
        params['nombre_marca'] = f'%{valor_busqueda}%'
    elif (campo_busqueda or valor_busqueda) or (campo_busqueda == "nada" and valor_busqueda):
        query += " ORDER BY M.ID_MARCA DESC"

    cursor = connection.cursor()
    cursor.execute(query, params)
    marcas_encontrados = cursor.fetchall()
    cursor.close()

    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=16)
    total_products = len(marcas_encontrados)
    start = (page - 1) * per_page
    end = start + per_page
    brands_to_display = marcas_encontrados[start:end]
    pagination = Pagination(page=page, per_page=per_page, total=total_products,
                            css_framework='bootstrap4', display_msg='{start} - {end} / {total}')

    if 'id_rol' in session:
        id_rol_u = session['id_rol']
        return render_template('resultadosBusquedaMarca.html', marcas=marcas_encontrados, marcas_encontrados=brands_to_display, pagination=pagination)
    else:
        return redirect(url_for('login'))

@app.route('/admin/users')  # Ruta para la página de usuarios
def users():
    cursor = connection.cursor()
    cursor.execute("SELECT U.ID_USUARIO, U.NOMBRE, U.CORREO, U.CONTRASENA, R.NOMBRE_ROL FROM USUARIOS U JOIN ROLES R ON U.ID_ROL = R.ID_ROL")
    usuarios = cursor.fetchall()
    cursor.close()

    cursor1 = connection.cursor()
    cursor1.execute("SELECT ID_ROL, NOMBRE_ROL FROM ROLES")
    roles = cursor1.fetchall()
    cursor1.close()

    # Verificar si los parámetros 'page' y 'per_page' se pasan en la solicitud GET
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=5)

    # Supongamos que tienes una lista de usuarios llamada 'usuarios'
    total_users = len(usuarios)

    # Calcula el índice de inicio y final para la página actual
    start = (page - 1) * per_page
    end = start + per_page

    # Obtiene los usuarios para la página actual
    users_to_display = usuarios[start:end]

    # Crea un objeto de paginación

    pagination = Pagination(page=page, per_page=per_page, total=total_users,
                            css_framework='bootstrap4', display_msg='Mostrando {start} - {end} de {total} categoria')
    if 'id_rol' in session:
        id_rol_u = session['id_rol']
        return render_template('users.html', usuarios=users_to_display, pagination=pagination, roles=roles)
    else:
        return redirect(url_for('login'))

@app.route('/crear_usuario', methods=['POST']) # Ruta para crear a Oracle los datos de usuarios
def crear_usuario():
    nombre = request.form.get('nombre')
    correo = request.form.get('correo')
    contrasena = request.form.get('contrasena')
    id_rol = request.form.get('id_rol')

    # Preparar la consulta SQL
    sql = "INSERT INTO usuarios (nombre, correo, contrasena, id_rol) VALUES (:nombre, :correo, :contrasena, :id_rol)"

    # Ejecutar la consulta
    cursor = connection.cursor()
    cursor.execute(sql, {'nombre': nombre, 'correo': correo,
                   'contrasena': contrasena, 'id_rol': id_rol})
    connection.commit()

    # variable de sesion
    session['mensaje'] = 'Usuario agregado correctamente'

    return redirect(url_for('users'))

@app.route('/editUsers/<int:ID_USUARIO>', methods=['GET', 'POST']) # ruta para editar usuarios
def editUsers(ID_USUARIO):
    if request.method == 'GET':
        try:
            # Realiza la conexión a tu base de datos Oracle
            dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
            connection = cx_Oracle.connect(
                user='USR_FERRETERIA', password='admin', dsn=dsn)

            # Crea un cursor
            cursor = connection.cursor()

            # Consulta SQL para obtener los datos del usuario por su ID
            query = "SELECT ID_USUARIO, nombre, correo, contrasena, id_rol FROM usuarios WHERE ID_USUARIO = :id_usuario"

            # Ejecuta la consulta con el ID_USUARIO como parámetro
            cursor.execute(query, id_usuario=ID_USUARIO)

            # Obtiene los datos del usuario
            usuario = cursor.fetchone()

            # Cierra el cursor y la conexión
            cursor.close()

            cursor1 = connection.cursor()
            cursor1.execute("SELECT ID_ROL, NOMBRE_ROL FROM ROLES")
            roles = cursor1.fetchall()
            cursor1.close()
            connection.close()

            if usuario is None:
                # Manejar el caso en el que no se encuentra el usuario
                flash('Usuario no encontrado', 'danger')
                # Redirige a la página de usuarios
                return redirect(url_for('users'))

            if 'id_rol' in session:
                id_rol_u = session['id_rol']
                return render_template('editUsers.html', usuario=usuario, roles=roles)
            else:
                return redirect(url_for('login'))

        except Exception as e:
            print("Error al obtener el usuario:", str(e))
            flash('Error al obtener el usuario', 'danger')
            # Redirige a la página de usuarios
            return redirect(url_for('users'))

    elif request.method == 'POST':
        try:
            # Realiza la conexión a tu base de datos Oracle
            dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
            connection = cx_Oracle.connect(
                user='USR_FERRETERIA', password='admin', dsn=dsn)

            # Crea un cursor
            cursor = connection.cursor()

            # Procesar el formulario de edición y actualizar los datos en la base de datos
            nombre = request.form.get('nombre')
            correo = request.form.get('correo')
            contrasena = request.form.get('contrasena')
            id_rol = request.form.get('id_rol')

            # Consulta SQL para actualizar los datos del usuario
            query = "UPDATE usuarios SET nombre = :nombre, correo = :correo, contrasena = :contrasena, id_rol = :id_rol WHERE ID_USUARIO = :id_usuario"

            # Ejecuta la consulta con los nuevos valores y el ID_USUARIO como parámetro
            cursor.execute(query, nombre=nombre, correo=correo,
                           contrasena=contrasena, id_rol=id_rol, id_usuario=ID_USUARIO)

            # Confirma la transacción
            connection.commit()

            # Cierra el cursor y la conexión
            cursor.close()
            connection.close()

            flash('Usuario actualizado con éxito', 'success')
            # Redirige de nuevo a la página de usuarios
            return redirect(url_for('users'))

        except Exception as e:
            print("Error al actualizar el usuario:", str(e))
            flash('Error al actualizar el usuario', 'danger')
            # Redirige a la página de usuarios
            return redirect(url_for('users'))

@app.route('/eliminar_usuario/<int:ID_USUARIO>', methods=['POST', 'DELETE']) # ruta para eliminar usuarios
def eliminar_usuario(ID_USUARIO):
    if request.method == 'POST' or request.form.get('_method') == 'DELETE':
        # Lógica para eliminar el usuario de la base de datos Oracle
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM USUARIOS WHERE ID_USUARIO = :ID_USUARIO", {
                           'ID_USUARIO': ID_USUARIO})
            connection.commit()
            flash('Usuario eliminado con éxito', 'success')
        except Exception as e:
            flash('Error al eliminar el usuario', 'danger')
        finally:
            cursor.close()

    return redirect(url_for('users'))

@app.route('/buscar_usuarios', methods=['POST'])  # ruta para buscar usuarios
def buscar_usuarios():
    campo_busqueda = request.form.get('campo_busqueda')
    valor_busqueda = request.form.get('valor_busqueda')

    # Consulta SQL parametrizada
    query = "SELECT * FROM usuarios WHERE 1=1"

    # Crear un diccionario de parámetros vacío
    params = {}

    if campo_busqueda == "nombre" and valor_busqueda:
        query += " AND nombre LIKE :nombre"
        params['nombre'] = f'%{valor_busqueda}%'
    elif campo_busqueda == "correo" and valor_busqueda:
        query += " AND correo LIKE :correo"
        params['correo'] = f'%{valor_busqueda}%'

    # Ejecutar la consulta y obtener los resultados
    cursor = connection.cursor()
    cursor.execute(query, params)
    usuarios_encontrados = cursor.fetchall()
    cursor.close()

    if 'id_rol' in session:
        id_rol_u = session['id_rol']
        return render_template('resultadosBusquedaUsuario.html', usuarios=usuarios_encontrados)
    else:
        return redirect(url_for('login'))

@app.route('/admin/contacts')  # Ruta para la página de contactos
def contacts():
    cursor = connection.cursor()
    cursor.execute("SELECT C.ID_CONTACTO, C.NOMBRE_CONTACTO, C.CORREO_CONTACTO, C.DIRECCION_CONTACTO, C.TELEFONO_CONTACTO, C.NIT_CONTACTO, C.IMAGEN_CONTACTO, R.NOMBRE_ROL FROM CONTACTOS C JOIN ROLES R ON C.ID_ROL = R.ID_ROL ORDER BY C.ID_CONTACTO DESC")
    contactos = cursor.fetchall()
    cursor.close()

    cursor1 = connection.cursor()
    cursor1.execute("SELECT ID_ROL, NOMBRE_ROL FROM ROLES")
    roles = cursor1.fetchall()
    cursor1.close()

    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=16)
    total_users = len(contactos)
    start = (page - 1) * per_page
    end = start + per_page
    contacts_to_display = contactos[start:end]
    pagination = Pagination(page=page, per_page=per_page, total=total_users,
                            css_framework='bootstrap4', display_msg='{start} - {end} / {total}')

    if 'id_rol' in session:
        id_rol_u = session['id_rol']
        return render_template('contacts.html', contactos=contacts_to_display, pagination=pagination, roles=roles)
    else:
        return redirect(url_for('login'))

@app.route('/newContacts')
def newContacts():
    cursor = connection.cursor()
    cursor.execute("SELECT ID_ROL, NOMBRE_ROL FROM ROLES")
    rolescontactos = cursor.fetchall()
    cursor.close()

    if 'id_rol' in session:
        id_rol = session['id_rol']
        return render_template('newContacts.html', rolescontactos=rolescontactos)
    else:
        return redirect(url_for('login'))

@app.route('/crear_contacto', methods=['POST']) # Ruta para crear a Oracle los datos del contacto
def crear_contacto():
    nombre_contacto = request.form.get('nombre_contacto')
    correo_contacto = request.form.get('correo_contacto')
    direccion_contacto = request.form.get('direccion_contacto')
    telefono_contacto = request.form.get('telefono_contacto')
    nit_contacto = request.form.get('nit_contacto')
    id_rol = request.form.get('id_rol')
    imagen_contacto = request.files['imagen_contacto']

    if imagen_contacto:
        # Guarda la imagen en la ruta static/imgbd
        imagen_contacto.save(os.path.join(
            'static/imgbd', imagen_contacto.filename))

        # Guarta la imagen en la base de datos empezando por imgbd/ seguido del nombre de la imagen
        ruta_imagen = os.path.join('imgbd/', imagen_contacto.filename)
    else:
        ruta_imagen = os.path.join('imgbd/no contacto.jpg')

    # Preparar la consulta SQL
    sql = "INSERT INTO contactos (nombre_contacto, correo_contacto, direccion_contacto, telefono_contacto, nit_contacto, id_rol, imagen_contacto) VALUES (:nombre_contacto, :correo_contacto, :direccion_contacto, :telefono_contacto, :nit_contacto, :id_rol, :imagen_contacto)"

    # Ejecutar la consulta
    cursor = connection.cursor()
    cursor.execute(sql, {'nombre_contacto': nombre_contacto, 'correo_contacto': correo_contacto, 'direccion_contacto': direccion_contacto,
                   'telefono_contacto': telefono_contacto, 'nit_contacto': nit_contacto, 'id_rol': id_rol, 'imagen_contacto': ruta_imagen})
    connection.commit()

    # variable de sesion
    session['mensaje'] = 'Contacto creado correctamente'

    return redirect(url_for('contacts'))

@app.route('/editContacts/<int:ID_CONTACTO>', methods=['GET', 'POST']) # ruta para editar contactos
def editContacts(ID_CONTACTO):
    if request.method == 'GET':
        try:
            dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
            connection = cx_Oracle.connect(user='USR_FERRETERIA', password='admin', dsn=dsn)
            cursor = connection.cursor()
            query = "SELECT ID_CONTACTO, nombre_contacto, correo_contacto, direccion_contacto, telefono_contacto, nit_contacto, id_rol, imagen_contacto FROM contactos WHERE ID_CONTACTO = :id_contacto"
            cursor.execute(query, id_contacto=ID_CONTACTO)
            contacto = cursor.fetchone()
            cursor.close()

            cursor2 = connection.cursor()
            cursor2.execute("SELECT ID_ROL, NOMBRE_ROL FROM ROLES")
            rolescontactos = cursor2.fetchall()
            cursor2.close()
            connection.close()

            if contacto is None:
                return redirect(url_for('contacts'))

            if 'id_rol' in session:
                id_rol_u = session['id_rol']
                return render_template('editContacts.html', contacto=contacto, rolescontactos=rolescontactos)
            else:
                return redirect(url_for('login'))

        except Exception as e:
            print("Error al obtener el contacto:", str(e))
            flash('Error al obtener el contacto', 'danger')
            return redirect(url_for('contacts'))

    elif request.method == 'POST':
        try:
            dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
            connection = cx_Oracle.connect(
                user='USR_FERRETERIA', password='admin', dsn=dsn)

            cursor = connection.cursor()

            nombre_contacto = request.form.get('nombre_contacto')
            correo_contacto = request.form.get('correo_contacto')
            direccion_contacto = request.form.get('direccion_contacto')
            telefono_contacto = request.form.get('telefono_contacto')
            nit_contacto = request.form.get('nit_contacto')
            id_rol = request.form.get('id_rol')

            cursor.execute("SELECT imagen_contacto FROM contactos WHERE ID_CONTACTO = :id_contacto", id_contacto=ID_CONTACTO)
            resultado = cursor.fetchone()
            imagen_actual = resultado[0] if resultado else None

            imagen_contacto = request.files.get('imagen_contacto')

            if imagen_contacto:
                imagen_contacto.save(os.path.join('static/imgbd', imagen_contacto.filename))
                ruta_imagen = os.path.join('imgbd/', imagen_contacto.filename)
            else:
                ruta_imagen = imagen_actual

            query = "UPDATE contactos SET nombre_contacto = :nombre_contacto, correo_contacto = :correo_contacto, direccion_contacto = :direccion_contacto, telefono_contacto = :telefono_contacto, nit_contacto = :nit_contacto, id_rol = :id_rol, imagen_contacto = :imagen_contacto WHERE ID_CONTACTO = :id_contacto"
            cursor.execute(query, nombre_contacto=nombre_contacto, correo_contacto=correo_contacto, direccion_contacto=direccion_contacto,
                           telefono_contacto=telefono_contacto, nit_contacto=nit_contacto, id_rol=id_rol, imagen_contacto=ruta_imagen, id_contacto=ID_CONTACTO)
            connection.commit()
            cursor.close()
            connection.close()

            flash('Contacto actualizado con éxito', 'success')
            return redirect(url_for('contacts'))

        except Exception as e:
            print("Error al actualizar el contacto:", str(e))
            flash('Error al actualizar el contacto', 'danger')
            return redirect(url_for('contacts'))

@app.route('/eliminar_contacto/<int:ID_CONTACTO>', methods=['POST', 'DELETE']) # ruta para eliminar contactos
def eliminar_contacto(ID_CONTACTO):
    if request.method == 'POST' or request.form.get('_method') == 'DELETE':
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM CONTACTOS WHERE ID_CONTACTO = :ID_CONTACTO", {
                           'ID_CONTACTO': ID_CONTACTO})
            connection.commit()
            flash('Contacto eliminado con éxito', 'success')
        except Exception as e:
            flash('Error al eliminar el contacto', 'danger')
        finally:
            cursor.close()

    return redirect(url_for('contacts'))

@app.route('/buscar_contactos', methods=['POST'])  # ruta para buscar contactos
def buscar_contactos():
    campo_busqueda = request.form.get('campo_busqueda')
    valor_busqueda = request.form.get('valor_busqueda')

    query = "SELECT C.ID_CONTACTO, C.NOMBRE_CONTACTO, C.CORREO_CONTACTO, C.DIRECCION_CONTACTO, C.TELEFONO_CONTACTO, C.NIT_CONTACTO, C.IMAGEN_CONTACTO FROM CONTACTOS C JOIN ROLES R ON C.ID_ROL = R.ID_ROL"
    params = {}

    if campo_busqueda == "nombre_contacto" and valor_busqueda:
        query += " WHERE 1=1 AND UPPER(nombre_contacto) LIKE UPPER(:nombre_contacto)"
        params['nombre_contacto'] = f'%{valor_busqueda}%'
    elif campo_busqueda == "nit_contacto" and valor_busqueda:
        query += " WHERE 1=1 AND UPPER(nit_contacto) LIKE UPPER(:nit_contacto)"
        params['nit_contacto'] = f'%{valor_busqueda}%'
    elif (campo_busqueda or valor_busqueda) or (campo_busqueda == "nada" and valor_busqueda):
        query += " ORDER BY C.ID_CONTACTO DESC"

    cursor = connection.cursor()
    cursor.execute(query, params)
    contactos_encontrados = cursor.fetchall()
    cursor.close()

    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=16)
    total_contacts = len(contactos_encontrados)
    start = (page - 1) * per_page
    end = start + per_page
    contacts_to_display = contactos_encontrados[start:end]
    pagination = Pagination(page=page, per_page=per_page, total=total_contacts,
                            css_framework='bootstrap4', display_msg='{start} - {end} / {total}')

    if 'id_rol' in session:
        id_rol_u = session['id_rol']
        return render_template('resultadosBusquedaContacto.html', contactos=contactos_encontrados, contactos_encontrados=contacts_to_display, pagination=pagination)
    else:
        return redirect(url_for('login'))

@app.route('/admin/sales')
def sales():
    cursor = connection.cursor()
    cursor.execute("SELECT NO_FACTURA, FECHA_EMISION, NOMBRE, NIT, DIRECCION, VENDEDOR, TOTAL FROM FACTURAS ORDER BY NO_FACTURA DESC")
    ventas = cursor.fetchall()
    cursor.close()

    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=16)
    total_users = len(ventas)
    start = (page - 1) * per_page
    end = start + per_page
    sales_to_display = ventas[start:end]
    pagination = Pagination(page=page, per_page=per_page, total=total_users,
                            css_framework='bootstrap4', display_msg='{start} - {end} / {total}')

    if 'id_rol' in session:
        id_rol = session['id_rol']
        return render_template('sales.html', ventas=sales_to_display, pagination=pagination)
    else:
        return redirect(url_for('login'))

@app.route('/newSales')
def newSales():
    cursor = connection.cursor()
    cursor.execute("SELECT *FROM PRODUCTOS")
    productos = cursor.fetchall()
    cursor.close()

    cursor1 = connection.cursor()
    cursor1.execute("SELECT (MAX(NO_FACTURA)+1) FROM FACTURAS")
    venta = cursor1.fetchone()
    cursor1.close()

    if 'id_rol' in session:
        id_rol = session['id_rol']
        return render_template('newSales.html', productos=productos, venta=venta)
    else:
        return redirect(url_for('login'))

@app.route('/crear_venta', methods=['POST'])
def crear_venta():
    nombre_rol_u = session['nombre']
    data = request.get_json()
    facturaItems = data['facturaItems']

    fecha_emision = data.get('fecha_emision')
    nombre = data.get('nombre')
    nit = int(data.get('nit'))
    direccion = data.get('direccion')

    sql = "INSERT INTO FACTURAS (FECHA_EMISION, NOMBRE, NIT, DIRECCION, VENDEDOR) VALUES (:fecha_emision, :nombre, :nit, :direccion, :vendedor)"

    cursor = connection.cursor()
    cursor.execute(sql, {'fecha_emision': fecha_emision, 'nombre': nombre, 'nit': nit, 'direccion': direccion, 'vendedor': nombre_rol_u})
    connection.commit()

    cursor.execute("SELECT FACTURAS_SEQ.CURRVAL FROM DUAL")
    no_factura = cursor.fetchone()[0]

    for producto in facturaItems:
        id_producto = producto['id_producto']
        cantidad = producto['cantidad']
        precio = producto['precio']
        subtotal = producto['subtotal']

        sql_detalle ="INSERT INTO DETALLES_FACTURA (NO_FACTURA, ID_PRODUCTO, CANTIDAD, PRECIO, SUBTOTAL) VALUES (:no_factura, :id_producto, :cantidad, :precio, :subtotal)"
        cursor.execute(sql_detalle, {'no_factura': no_factura, 'id_producto': id_producto, 'cantidad': cantidad, 'precio': precio, 'subtotal': subtotal})
        connection.commit()

    cursor.close()

    if 'id_rol' in session:
        id_rol = session['id_rol']
        nombre_rol_u = session['nombre']
        print(nombre_rol_u)
        return redirect(url_for('newSales'))
    else:
        return redirect(url_for('login'))

@app.route('/editSales/<int:NO_FACTURA>', methods=['GET', 'POST'])
def editSales(NO_FACTURA):
    if request.method == 'GET':
        try:
            dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
            connection = cx_Oracle.connect(user='USR_FERRETERIA', password='admin', dsn=dsn)

            cursor = connection.cursor()
            query = "SELECT F.NO_FACTURA, F.NOMBRE, F.NIT, F.DIRECCION, F.FECHA_EMISION, D.ID_DETALLE, P.NOMBRE_PRODUCTO, D.CANTIDAD, D.PRECIO, P.EXISTENCIA, D.SUBTOTAL FROM FACTURAS F JOIN DETALLES_FACTURA D ON D.NO_FACTURA = F.NO_FACTURA JOIN PRODUCTOS P ON P.ID_PRODUCTO = D.ID_PRODUCTO WHERE F.NO_FACTURA = :no_factura ORDER BY D.ID_DETALLE ASC"
            cursor.execute(query, no_factura=NO_FACTURA)
            venta = cursor.fetchone()
            cursor.close()

            cursor1 = connection.cursor()
            cursor1.execute("SELECT F.NO_FACTURA, F.NOMBRE, F.NIT, F.DIRECCION, F.FECHA_EMISION, D.ID_DETALLE, P.NOMBRE_PRODUCTO, D.CANTIDAD, D.PRECIO, P.EXISTENCIA, D.SUBTOTAL FROM FACTURAS F JOIN DETALLES_FACTURA D ON D.NO_FACTURA = F.NO_FACTURA JOIN PRODUCTOS P ON P.ID_PRODUCTO = D.ID_PRODUCTO WHERE F.NO_FACTURA = :no_factura ORDER BY D.ID_DETALLE ASC")
            tablas = cursor1.fetchall()
            cursor1.close()

            cursor2 = connection.cursor()
            cursor2.execute("SELECT *FROM PRODUCTOS")
            productos = cursor2.fetchall()
            cursor2.close()
            connection.close()

            if venta is None:
                flash('venta no encontrada', 'danger')
                return redirect(url_for('sales'))
            if 'id_rol' in session:
                id_rol_u = session['id_rol']
                return render_template('editSales.html', venta=venta, tablas=tablas, productos=productos)
            else:
                return redirect(url_for('login'))

        except Exception as e:
            print("Error al obtener la venta:", str(e))
            flash('Error al obtener la venta', 'danger')
            return redirect(url_for('sales'))

    elif request.method == 'POST':
        try:
            dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
            connection = cx_Oracle.connect(
                user='USR_FERRETERIA', password='admin', dsn=dsn)

            cursor = connection.cursor()
            cursor1 = connection.cursor()

            data = request.get_json()
            facturaItems = data['facturaItems']

            nombre = data.get('nombre')
            nit = int(data.get('nit'))
            direccion = data.get('direccion')

            query = "UPDATE FACTURAS SET nombre = :nombre, nit = :nit, direccion = :direccion WHERE NO_FACTURA = :no_factura"
            cursor.execute(query, nombre=nombre, nit=nit, direccion=direccion, no_factura=NO_FACTURA)
            connection.commit()
            cursor.close()


            for producto in facturaItems:
                no_factura = producto['no_factura']
                id_producto = producto['id_producto']
                cantidad = producto['cantidad']
                precio = producto['precio']
                subtotal = producto['subtotal']

                sql_detalle ="INSERT INTO DETALLES_FACTURA (NO_FACTURA, ID_PRODUCTO, CANTIDAD, PRECIO, SUBTOTAL) VALUES (:no_factura, :id_producto, :cantidad, :precio, :subtotal)"
                cursor1.execute(sql_detalle, {'no_factura': no_factura, 'id_producto': id_producto, 'cantidad': cantidad, 'precio': precio, 'subtotal': subtotal})
                connection.commit()

            cursor1.close()

            connection.close()

            flash('Factura actualizado con éxito', 'success')
            return redirect(url_for('sales'))

        except Exception as e:
            print("Error al actualizar el factura:", str(e))
            flash('Error al actualizar el factura', 'danger')
            return redirect(url_for('sales'))

@app.route('/actualizar_cantidades', methods=['POST'])
def actualizar_cantidades():
    if request.method == 'POST':
        selected_items = request.form.getlist('items')
        cursor2 = connection.cursor()

        for item in selected_items:
            cantidad = request.form.get('cantidad_' + item)
            subtotal = request.form.get('subtotal_' + item)  # Adjust the name to match your HTML

            # Define the SQL statement with placeholders for cantidad and id_detalle
            sql_detalle = "UPDATE DETALLES_FACTURA SET CANTIDAD = :cantidad, SUBTOTAL = :subtotal WHERE ID_DETALLE = :id_detalle"

            # Execute the update for each item
            cursor2.execute(sql_detalle, cantidad=cantidad, subtotal=subtotal, id_detalle=item)
            connection.commit()

        cursor2.close()  # Close the cursor after all updates are done
        return redirect(request.referrer)

@app.route('/eliminar_venta/<int:ID_DETALLE>', methods=['POST'])
def eliminar_venta(ID_DETALLE):
    if request.method == 'POST':
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM DETALLES_FACTURA WHERE ID_DETALLE = :ID_DETALLE", {
                           'ID_DETALLE': ID_DETALLE})
            connection.commit()
            flash('Venta eliminada con éxito', 'success')
        except Exception as e:
            flash('Error al eliminar la venta', 'danger')
        finally:
            cursor.close()

    return redirect(request.referrer)

@app.route('/buscar_ventas', methods=['POST'])
def buscar_ventas():
    campo_busqueda = request.form.get('campo_busqueda')
    valor_busqueda = request.form.get('valor_busqueda')

    query = "SELECT NO_FACTURA, FECHA_EMISION, NOMBRE, NIT, DIRECCION FROM FACTURAS"
    params = {}

    if campo_busqueda == "nombre" and valor_busqueda:
        query += " WHERE 1=1 AND UPPER(nombre) LIKE UPPER(:nombre)"
        params['nombre'] = f'%{valor_busqueda}%'
    elif campo_busqueda == "no_factura" and valor_busqueda:
        query += " WHERE 1=1 AND no_factura LIKE :no_factura"
        params['no_factura'] = f'%{valor_busqueda}%'
    elif (campo_busqueda or valor_busqueda) or (campo_busqueda == "nada" and valor_busqueda):
        query += " ORDER BY NO_FACTURA DESC"

    cursor = connection.cursor()
    cursor.execute(query, params)
    facturas_encontrados = cursor.fetchall()
    cursor.close()

    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=16)
    total_contacts = len(facturas_encontrados)
    start = (page - 1) * per_page
    end = start + per_page
    sales_to_display = facturas_encontrados[start:end]
    pagination = Pagination(page=page, per_page=per_page, total=total_contacts,
                            css_framework='bootstrap4', display_msg='{start} - {end} / {total}')

    if 'id_rol' in session:
        id_rol_u = session['id_rol']
        return render_template('resultadosBusquedaVenta.html', ventas=facturas_encontrados, facturas_encontrados=sales_to_display, pagination=pagination)
    else:
        return redirect(url_for('login'))

@app.route('/admin/purchases')
def purchases():
    cursor = connection.cursor()
    cursor.execute("SELECT C.NO_COMPRA, C.FECHA_PEDIDO, C.PROVEEDOR, C.DIRECCION, C.COMPRADOR, C.TOTAL FROM COMPRAS C ORDER BY C.NO_COMPRA DESC")
    compras = cursor.fetchall()
    cursor.close()

    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=16)
    total_users = len(compras)
    start = (page - 1) * per_page
    end = start + per_page
    purchases_to_display = compras[start:end]
    pagination = Pagination(page=page, per_page=per_page, total=total_users,
                            css_framework='bootstrap4', display_msg='{start} - {end} / {total}')

    if 'id_rol' in session:
        id_rol = session['id_rol']
        return render_template('purchases.html', compras=purchases_to_display, pagination=pagination)
    else:
        return redirect(url_for('login'))

@app.route('/newPurchases')
def newPurchases():
    cursor = connection.cursor()
    cursor.execute("SELECT *FROM PRODUCTOS")
    productos = cursor.fetchall()
    cursor.close()

    cursor1 = connection.cursor()
    cursor1.execute("SELECT (MAX(NO_COMPRA)+1) FROM COMPRAS")
    compra = cursor1.fetchone()
    cursor1.close()

    if 'id_rol' in session:
        id_rol = session['id_rol']
        return render_template('newPurchases.html', productos=productos, compra=compra)
    else:
        return redirect(url_for('login'))

@app.route('/crear_compra', methods=['POST'])
def crear_compra():
    nombre_rol_u = session['nombre']
    data = request.get_json()
    facturaItems = data['facturaItems']

    fecha_pedido = data.get('fecha_pedido')
    nombre = data.get('nombre')
    direccion = data.get('direccion')

    sql = "INSERT INTO COMPRAS (FECHA_PEDIDO, PROVEEDOR, DIRECCION, COMPRADOR) VALUES (:fecha_pedido, :proveedor, :direccion, :comprador)"

    cursor = connection.cursor()
    cursor.execute(sql, {'fecha_pedido': fecha_pedido, 'proveedor': nombre, 'direccion': direccion, 'comprador': nombre_rol_u})
    connection.commit()

    cursor.execute("SELECT COMPRAS_SEQ.CURRVAL FROM DUAL")
    no_compra = cursor.fetchone()[0]

    for producto in facturaItems:
        id_producto = producto['id_producto']
        cantidad = producto['cantidad']
        precio = producto['precio']
        subtotal = producto['subtotal']

        sql_detalle ="INSERT INTO DETALLES_COMPRA (NO_COMPRA, ID_PRODUCTO, CANTIDAD, PRECIO, SUBTOTAL) VALUES (:no_compra, :id_producto, :cantidad, :precio, :subtotal)"
        cursor.execute(sql_detalle, {'no_compra': no_compra, 'id_producto': id_producto, 'cantidad': cantidad, 'precio': precio, 'subtotal': subtotal})
        connection.commit()

    cursor.close()

    if 'id_rol' in session:
        id_rol = session['id_rol']
        nombre_rol_u = session['nombre']
        print(nombre_rol_u)
        return redirect(url_for('newPurchases'))
    else:
        return redirect(url_for('login'))

@app.route('/editPurchases/<int:NO_COMPRA>', methods=['GET', 'POST'])
def editPurchases(NO_COMPRA):
    if request.method == 'GET':
        try:
            dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
            connection = cx_Oracle.connect(user='USR_FERRETERIA', password='admin', dsn=dsn)

            cursor = connection.cursor()
            query = "SELECT F.NO_COMPRA, F.PROVEEDOR, F.DIRECCION, F.FECHA_PEDIDO, D.ID_DETALLEC, P.NOMBRE_PRODUCTO, D.CANTIDAD, D.PRECIO, P.EXISTENCIA, D.SUBTOTAL FROM COMPRAS F JOIN DETALLES_COMPRA D ON D.NO_COMPRA = F.NO_COMPRA JOIN PRODUCTOS P ON P.ID_PRODUCTO = D.ID_PRODUCTO WHERE F.NO_COMPRA = :no_compra ORDER BY D.ID_DETALLEC ASC"
            cursor.execute(query, no_compra=NO_COMPRA)
            compra = cursor.fetchone()
            cursor.close()

            cursor1 = connection.cursor()
            cursor1.execute("SELECT F.NO_COMPRA, F.PROVEEDOR, F.DIRECCION, F.FECHA_PEDIDO, D.ID_DETALLEC, P.NOMBRE_PRODUCTO, D.CANTIDAD, D.PRECIO, P.EXISTENCIA, D.SUBTOTAL FROM COMPRAS F JOIN DETALLES_COMPRA D ON D.NO_COMPRA = F.NO_COMPRA JOIN PRODUCTOS P ON P.ID_PRODUCTO = D.ID_PRODUCTO WHERE F.NO_COMPRA = :no_compra ORDER BY D.ID_DETALLEC ASC")
            tablas = cursor1.fetchall()
            cursor1.close()

            cursor2 = connection.cursor()
            cursor2.execute("SELECT *FROM PRODUCTOS")
            productos = cursor2.fetchall()
            cursor2.close()
            connection.close()

            if compra is None:
                flash('compra no encontrada', 'danger')
                return redirect(url_for('purchases'))
            if 'id_rol' in session:
                id_rol_u = session['id_rol']
                return render_template('editPurchases.html', compra=compra, tablas=tablas, productos=productos)
            else:
                return redirect(url_for('login'))

        except Exception as e:
            print("Error al obtener la compra:", str(e))
            flash('Error al obtener la compra', 'danger')
            return redirect(url_for('purchases'))

    elif request.method == 'POST':
        try:
            dsn = cx_Oracle.makedsn(host='localhost', port=1521, sid='xe')
            connection = cx_Oracle.connect(
                user='USR_FERRETERIA', password='admin', dsn=dsn)

            cursor = connection.cursor()
            cursor1 = connection.cursor()

            data = request.get_json()
            facturaItems = data['facturaItems']

            proveedor = data.get('nombre')
            direccion = data.get('direccion')

            query = "UPDATE COMPRAS SET proveedor = :proveedor, direccion = :direccion WHERE NO_COMPRA = :no_compra"
            cursor.execute(query, proveedor=proveedor, direccion=direccion, no_compra=NO_COMPRA)
            connection.commit()
            cursor.close()


            for producto in facturaItems:
                no_compra = producto['no_compra']
                id_producto = producto['id_producto']
                cantidad = producto['cantidad']
                precio = producto['precio']
                subtotal = producto['subtotal']

                sql_detalle ="INSERT INTO DETALLES_COMPRA (NO_COMPRA, ID_PRODUCTO, CANTIDAD, PRECIO, SUBTOTAL) VALUES (:no_compra, :id_producto, :cantidad, :precio, :subtotal)"
                cursor1.execute(sql_detalle, {'no_compra': no_compra, 'id_producto': id_producto, 'cantidad': cantidad, 'precio': precio, 'subtotal': subtotal})
                connection.commit()

            cursor1.close()

            connection.close()

            flash('Compra actualizado con éxito', 'success')
            return redirect(url_for('purchases'))

        except Exception as e:
            print("Error al actualizar el compra:", str(e))
            flash('Error al actualizar el compra', 'danger')
            return redirect(url_for('purchases'))

@app.route('/actualizar_cantidadesc', methods=['POST'])
def actualizar_cantidadesc():
    if request.method == 'POST':
        selected_items = request.form.getlist('items')
        cursor2 = connection.cursor()

        for item in selected_items:
            cantidad = request.form.get('cantidad_' + item)
            subtotal = request.form.get('subtotal_' + item)  # Adjust the name to match your HTML

            # Define the SQL statement with placeholders for cantidad and id_detalle
            sql_detalle = "UPDATE DETALLES_COMPRA SET CANTIDAD = :cantidad, SUBTOTAL = :subtotal WHERE ID_DETALLEC = :id_detallec"

            # Execute the update for each item
            cursor2.execute(sql_detalle, cantidad=cantidad, subtotal=subtotal, id_detalleC=item)
            connection.commit()

        cursor2.close()  # Close the cursor after all updates are done
        return redirect(request.referrer)

@app.route('/eliminar_compra/<int:ID_DETALLEC>', methods=['POST', 'DELETE'])
def eliminar_compra(ID_DETALLEC):
    if request.method == 'POST':
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM DETALLES_COMPRA WHERE ID_DETALLEC = :ID_DETALLEC", {
                           'ID_DETALLEC': ID_DETALLEC})
            connection.commit()
            flash('compra eliminada con éxito', 'success')
        except Exception as e:
            flash('Error al eliminar la compra', 'danger')
        finally:
            cursor.close()

    return redirect(request.referrer)

@app.route('/buscar_compras', methods=['POST'])
def buscar_compras():
    campo_busqueda = request.form.get('campo_busqueda')
    valor_busqueda = request.form.get('valor_busqueda')

    query = "SELECT NO_COMPRA, FECHA_PEDIDO, PROVEEDOR, DIRECCION, COMPRADOR, TOTAL FROM COMPRAS"
    params = {}

    if campo_busqueda == "nombre" and valor_busqueda:
        query += " WHERE 1=1 AND UPPER(proveedor) LIKE UPPER(:proveedor)"
        params['proveedor'] = f'%{valor_busqueda}%'
    elif campo_busqueda == "no_compra" and valor_busqueda:
        query += " WHERE 1=1 AND no_compra LIKE :no_compra"
        params['no_compra'] = f'%{valor_busqueda}%'
    elif (campo_busqueda or valor_busqueda) or (campo_busqueda == "nada" and valor_busqueda):
        query += " ORDER BY NO_COMPRA DESC"

    cursor = connection.cursor()
    cursor.execute(query, params)
    facturas_encontrados = cursor.fetchall()
    cursor.close()

    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=16)
    total_contacts = len(facturas_encontrados)
    start = (page - 1) * per_page
    end = start + per_page
    sales_to_display = facturas_encontrados[start:end]
    pagination = Pagination(page=page, per_page=per_page, total=total_contacts,
                            css_framework='bootstrap4', display_msg='{start} - {end} / {total}')

    if 'id_rol' in session:
        id_rol_u = session['id_rol']
        return render_template('resultadosBusquedaCompra.html', compras=facturas_encontrados, facturas_encontrados=sales_to_display, pagination=pagination)
    else:
        return redirect(url_for('login'))


@app.route('/generar_factura', methods=['POST'])
def generar_factura():
    
    datos_factura = request.json
    detalles_factura = datos_factura.get('detalles', [])

    nombre_cliente = datos_factura.get('cliente', 'Nombre no proporcionado')
    nit_cliente = datos_factura.get('nit', 'NIT no proporcionado')
    direccion_cliente = datos_factura.get('direccion', 'Direccion no proporcionada')
    fecha = datos_factura.get('fecha_emision', 'Fecha no proporcionada')
    no_factura = datos_factura.get('no_factura', 'Nofactura no proporcionada')

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    # Configurar el tamaño de la página
    width, height = 400, 450
    p.setPageSize((width, height))

    # Agregar encabezado
    p.setFont("Helvetica", 10)
    p.drawString(10, height - 20, "Ferretería \"La esquina\"")
    p.drawString(10, height - 30, "3a Calle Zona 1, San Lucas Sacatepéquez")
    p.drawString(10, height - 40, "Teléfono: ")

    p.line(10, height - 60, width - 10, height - 60)
    p.line(10, height - 105, width - 10, height - 105)
    p.line(10, height - 60, 10, height - 105)
    p.line(width - 10, height - 105, width - 10, height - 60)

        # Agregar una imagen al recibo (ajusta la ruta de la imagen)
    imagen_path = 'static/img/Logo.jpg'
    p.drawImage(imagen_path, 300, 395, 80, 50)

    # Agregar información del negocio
    p.setFont("Helvetica", 10)
    p.drawString(12, height - 75, "Cliente: " + nombre_cliente)
    p.drawString(12, height - 85, "Nit: " + nit_cliente)
    p.drawString(12, height - 95, "Dirección: " + direccion_cliente)
    p.drawString(250, height - 85, "Fecha: " + fecha)
    p.drawString(250, height - 75, "Factura No. " + no_factura)

    # Agregar línea separadora
    p.line(10, height - 110, width - 10, height - 110)
    p.line(10, height - 325, 10, height - 110)
    p.line(width - 10, height - 110, width - 10, height - 325)
    p.line(10, height - 122, width - 10, height - 122)

    p.drawString(12, height - 120, "Cantidad")
    p.drawString(120, height - 120, "Descripción")
    p.drawString(250, height - 120, "Precio")
    p.drawString(345, height - 120, "Total")

    y_position = height - 140 # Posición inicial para mostrar los detalles
    subtotal1 = 0
    iva = 0.12
    total_venta = 0
    for detalle in detalles_factura:
        producto = detalle.get('producto', 'Producto no especificado')
        cantidad = detalle.get('cantidad', 0)
        precio_unitario = detalle.get('precio_unitario', 0)
        subtotal = detalle.get('subtotal', 0)

        # Mostrar los detalles del producto en el PDF
        p.drawString(24, y_position, f"{cantidad}")
        p.drawString(120, y_position, f"{producto}")
        p.drawString(250, y_position, f"Q{precio_unitario:.2f}")
        p.drawString(340, y_position, f"Q{subtotal:.2f}")
        subtotal1 += precio_unitario * cantidad

        sql = "INSERT INTO VENTAS (NO_VENTA, NOMBRE, NIT, DIRECCION, FECHA, PRODUCTO, CANTIDAD, PRECIO, SUBTOTAL) VALUES (:no_venta, :nombre, :nit, :direccion, :fecha, :producto, :cantidad, :precio, :subtotal)"

        cursor = connection.cursor()
        cursor.execute(sql, {'no_venta': no_factura, 'nombre':nombre_cliente, 'nit':nit_cliente, 'direccion':direccion_cliente, 'fecha':fecha, 'producto':producto, 'cantidad':cantidad, 'precio':precio_unitario, 'subtotal':subtotal})
        connection.commit()

        y_position -= 12

    p.line(10, height - 325, width - 10, height - 325)

    p.drawString(300, height - 350, f"Subtotal:")
    p.drawString(350, height - 350, f"Q{subtotal1:.2f}")
    total_iva = subtotal1 * iva
    p.drawString(300, height - 360, f"Iva:")
    p.drawString(350, height - 360, f"Q{total_iva:.2f}")
    total_venta = total_iva + subtotal1
    p.drawString(300, height - 370, f"Total:")
    p.drawString(350, height - 370, f"Q{total_venta:.2f}")
    
 # Guardar el PDF
    p.showPage()
    p.save()
    # Aquí deberías generar el PDF con ReportLab y devolverlo como respuesta
    # Ejemplo simulado de devolver un PDF
    buffer.seek(0)
    response = Response(buffer)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Factura.pdf'
    return response

@app.route('/enviar_factura', methods=['POST'])
def enviar_factura():
    # Genera la factura como lo hacías anteriormente
    factura_pdf = generar_factura()

    # Simula el envío a través de una API (cambiar por la URL y datos según la API real)
    url_api_simulada = 'https://ejemplo.com/api/enviar_factura'
    datos_factura = {
        'archivo': factura_pdf,  # Aquí envías el PDF generado
        'cliente': 'Cliente de ejemplo',
        'monto': 100.0
        # Agrega otros datos necesarios para el envío simulado
    }

    # Simula la solicitud POST a la API
    response = requests.post(url_api_simulada, json=datos_factura)

    if response.status_code == 200:
        return "Factura enviada exitosamente"
    else:
        return "Error al enviar la factura"


@app.route('/generar_compra', methods=['POST'])
def generar_compra():
    datos_compra = request.json
    detalles_compra = datos_compra.get('detalles', [])

    nombre_proveedor = datos_compra.get('cliente', 'Nombre no proporcionado')
    direccion_cliente = datos_compra.get('direccion', 'Direccion no proporcionada')
    fecha = datos_compra.get('fecha_pedido', 'Fecha no proporcionada')
    no_factura = datos_compra.get('no_compra', 'Nofactura no proporcionada')

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    # Configurar el tamaño de la página
    width, height = 400, 400
    p.setPageSize((width, height))

    # Agregar encabezado
    p.setFont("Helvetica", 12)
    p.drawString(10, height - 20, "Ferretería \"La esquina\"")
        # Agregar una imagen al recibo (ajusta la ruta de la imagen)
    # imagen_path = 'static/img/logo_recibo.jpg'
    # p.drawImage(imagen_path, 350, 350, 50, 50)

    # Agregar información del negocio
    p.setFont("Helvetica", 10)
    p.drawString(10, height - 80, "Proveedor: " + nombre_proveedor)
    p.drawString(250, height - 90, "Dirección: " + direccion_cliente)
    p.drawString(250, height - 80, "Fecha: " + fecha)
    p.drawString(250, height - 70, "Orden de Compra No. " + no_factura)

    # Agregar línea separadora
    p.line(10, height - 100, width - 10, height - 100)

    p.drawString(10, height - 120, "Cantidad")
    p.drawString(120, height - 120, "Concepto")
    p.drawString(250, height - 120, "Precio")
    p.drawString(350, height - 120, "Total")

    y_position = height - 140 # Posición inicial para mostrar los detalles
    total_compra = 0
    for detalle in detalles_compra:
        producto = detalle.get('producto', 'Producto no especificado')
        cantidad = detalle.get('cantidad', 0)
        precio_unitario = detalle.get('precio_unitario', 0)
        subtotal = detalle.get('subtotal', 0)

        # Mostrar los detalles del producto en el PDF
        p.drawString(120, y_position, f"{producto}")
        p.drawString(20, y_position, f"{cantidad}")
        p.drawString(250, y_position, f"Q"+str(precio_unitario))
        p.drawString(350, y_position, f"Q"+str(subtotal))
        total_compra += precio_unitario * cantidad
        sql = "INSERT INTO ORDENES (ORDEN_COMPRA, PROVEEDOR, DIRECCION, FECHA, PRODUCTO, CANTIDAD, PRECIO, SUBTOTAL) VALUES (:orden_compra, :proveedor, :direccion, :fecha, :producto, :cantidad, :precio, :subtotal)"

        cursor = connection.cursor()
        cursor.execute(sql, {'orden_compra': no_factura, 'proveedor':nombre_proveedor, 'direccion':direccion_cliente, 'fecha':fecha, 'producto':producto, 'cantidad':cantidad, 'precio':precio_unitario, 'subtotal':subtotal})
        connection.commit()

        y_position -= 10
    p.line(10, height - 325, width - 10, height - 325)
    p.drawString(300, 50, f"Total: Q"+str(total_compra))


 # Guardar el PDF
    p.showPage()
    p.save()
    # Aquí deberías generar el PDF con ReportLab y devolverlo como respuesta
    # Ejemplo simulado de devolver un PDF
    buffer.seek(0)
    response = Response(buffer)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=OC.pdf'

    return response

if __name__ == '__main__':
    app.run(debug=True)
    #app.run(host='0.0.0.0', port=80)
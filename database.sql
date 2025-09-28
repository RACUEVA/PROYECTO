-- database.sql
-- Script de creación de la base de datos para Librería y Papelería Cueva

CREATE DATABASE IF NOT EXISTS papeleria_cueva;
USE papeleria_cueva;

-- Tabla de productos
CREATE TABLE IF NOT EXISTS productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL UNIQUE,
    cantidad INT NOT NULL DEFAULT 0,
    precio DECIMAL(10, 2) NOT NULL DEFAULT 0.0
);

-- Tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    apellido VARCHAR(120) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    email VARCHAR(120) UNIQUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de usuarios (para el sistema de login)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Datos de ejemplo
INSERT IGNORE INTO productos (nombre, cantidad, precio) VALUES
('Lápiz HB', 100, 1.00),
('Borrador', 50, 0.50),
('Cuaderno Universitario', 30, 3.50),
('Bolígrafo Azul', 200, 1.25);

INSERT IGNORE INTO clientes (nombre, apellido, telefono, email) VALUES
('Juan', 'Pérez', '0987654321', 'juan@email.com'),
('María', 'Gómez', '0991234567', 'maria@email.com');
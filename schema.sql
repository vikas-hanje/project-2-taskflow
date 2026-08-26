CREATE DATABASE Taskflow_DB;

USE Taskflow_DB;

CREATE TABLE users (
    user_id CHAR(36) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE projects (
    project_id CHAR(36) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id CHAR(36) NOT NULL,
    CONSTRAINT fk_users
        FOREIGN KEY (user_id) 
        REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE tasks (
    task_id CHAR(36) PRIMARY KEY,
    title VARCHAR(50) NOT NULL,
    status ENUM('To Do', 'In Progress', 'Completed') NOT NULL DEFAULT 'To Do',
    due_date DATETIME,
    priority ENUM('Low', 'Medium', 'High') NOT NULL DEFAULT 'Medium',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    project_id CHAR(36) NOT NULL,
    CONSTRAINT fk_projects
        FOREIGN KEY (project_id) 
        REFERENCES projects(project_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
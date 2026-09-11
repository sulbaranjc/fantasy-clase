-- 005_alumnos_username_unico_global.sql
-- El login de alumno debe ser simple (usuario + contraseña, sin pedirle
-- que además indique de qué clase es). Con el username único solo POR
-- CLASE (migración 001), un mismo usuario podría existir en dos clases
-- distintas del profesor y el login sería ambiguo. Como el sistema no es
-- multi-profesor (un solo profesor, varias clases propias), se simplifica
-- a un espacio de nombres único entre TODOS los alumnos de TODAS sus
-- clases.
--
-- `uq_alumnos_username_clase (clase_id, username)` respalda también la FK
-- fk_alumnos_clase (clase_id), así que MySQL no deja eliminarlo sin antes
-- darle a esa FK un índice de soporte propio.

ALTER TABLE alumnos
    ADD INDEX idx_alumnos_clase (clase_id);

ALTER TABLE alumnos
    DROP INDEX uq_alumnos_username_clase;

ALTER TABLE alumnos
    ADD UNIQUE KEY uq_alumnos_username (username);

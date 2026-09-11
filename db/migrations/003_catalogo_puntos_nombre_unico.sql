-- 003_catalogo_puntos_nombre_unico.sql
-- Evita duplicar por accidente un mismo tipo de evento dentro de la misma
-- clase (ej. dar de alta "Examen >9" dos veces con distinta puntuación).

ALTER TABLE catalogo_puntos
    ADD UNIQUE KEY uq_catalogo_puntos_clase_nombre (clase_id, nombre);

-- Migration 002: Add recurso column to servicios_adicionales
-- RF-11: Validar traslapes por recurso (sala/masajista)

ALTER TABLE servicios_adicionales
ADD COLUMN recurso VARCHAR(100);

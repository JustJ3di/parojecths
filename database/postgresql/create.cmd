rem @echo off
set PATH=%PATH%;C:\Program Files\PostgreSQL\11\bin
dropdb -h localhost -U postgres spritz
createdb -h localhost -U postgres spritz
psql -h localhost -U postgres spritz < create.sql
pause
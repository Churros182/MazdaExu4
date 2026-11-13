# Mazda Calibration Files Android

Proyecto base en Kotlin configurado con **GitHub Actions** para compilar el `.apk` directamente en la nube sin necesidad de PC.

## Cómo compilar el APK desde el celular

1. Crea una cuenta o inicia sesión en [GitHub](https://github.com) desde el navegador de tu teléfono.
2. Crea un nuevo repositorio público o privado (por ejemplo: `MazdaVBFFlasher`).
3. Descomprime este archivo `.zip` en tu teléfono y sube todos los archivos y carpetas manteniendo la misma estructura (asegúrate de incluir la carpeta oculta `.github/workflows/build_apk.yml`).
4. Ve a la pestaña **Actions** dentro de tu repositorio en GitHub.
5. Verás un flujo de trabajo llamado **Build Android APK** ejecutándose (tarda unos 2-3 minutos).
6. Al terminar (marca verde ✅), entra a la ejecución, baja hasta la sección **Artifacts** y descarga **MazdaVBFFlasher-Debug**.
7. Descomprime el archivo descargado en tu celular e instala el `.apk`.

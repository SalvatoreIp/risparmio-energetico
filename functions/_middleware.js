// Rinvio permanente da www.guida-energia.com a guida-energia.com:
// senza questo Google vede due copie dello stesso sito.
export async function onRequest({ request, next }) {
  const url = new URL(request.url);
  if (url.hostname === "www.guida-energia.com") {
    url.hostname = "guida-energia.com";
    return Response.redirect(url.toString(), 301);
  }
  return next();
}

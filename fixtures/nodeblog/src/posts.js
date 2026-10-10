export function slugify(title) {
  return title.toLowerCase().trim().replace(/\s+/g, "-");
}
export function excerpt(body, n = 80) {
  return body.length <= n ? body : body.slice(0, n) + "...";
}

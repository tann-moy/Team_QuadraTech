
document.addEventListener("DOMContentLoaded", function () {
  var el = document.getElementById("map-picker");
  if (!el) return;
  var latInput = document.getElementById(el.dataset.latInput);
  var lngInput = document.getElementById(el.dataset.lngInput);
  var hasPoint = latInput.value && lngInput.value;
  var start = hasPoint ? [parseFloat(latInput.value), parseFloat(lngInput.value)] : [23.8103, 90.4125]; // Dhaka
  var map = L.map(el).setView(start, hasPoint ? 14 : 11);
 L.tileLayer(
        "https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
        {
            subdomains: "abc",
            maxZoom: 19,
            attribution:
                '&copy; OpenStreetMap contributors, Tiles style by HOT'
        }
    ).addTo(map);
  var marker = hasPoint ? L.marker(start).addTo(map) : null;

  function setPoint(lat, lng) {
    latInput.value = lat.toFixed(6);
    lngInput.value = lng.toFixed(6);
    if (marker) marker.setLatLng([lat, lng]); else marker = L.marker([lat, lng]).addTo(map);
  }
  map.on("click", function (e) { setPoint(e.latlng.lat, e.latlng.lng); });

  var locate = document.getElementById("locate-btn");
  if (locate) locate.addEventListener("click", function () {
    navigator.geolocation.getCurrentPosition(function (p) {
      setPoint(p.coords.latitude, p.coords.longitude);
      map.setView([p.coords.latitude, p.coords.longitude], 15);
    });
  });

  var searchBtn = document.getElementById("map-search-btn");
  if (searchBtn) searchBtn.addEventListener("click", function () {
    var q = document.getElementById("map-search").value;
    if (!q) return;
    fetch("https://nominatim.openstreetmap.org/search?format=json&limit=1&q=" + encodeURIComponent(q))
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.length) {
          var lat = parseFloat(res[0].lat), lng = parseFloat(res[0].lon);
          setPoint(lat, lng); map.setView([lat, lng], 15);
        }
      });
  });
});

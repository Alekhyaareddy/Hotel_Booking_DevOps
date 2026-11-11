const hotels = [
  {
    id: "cove",
    name: "The Cove at Nusa Dua",
    location: "Bali, Indonesia",
    search: "bali indonesia nusa dua coast",
    type: "suite",
    room: "Garden suite",
    price: 248,
    rating: "4.92",
    reviews: "128 stays",
    tag: "The slow-life edit",
    description: "A tucked-away coastal hideout where the days drift between garden paths and the Indian Ocean.",
    amenities: ["Ocean air", "Private terrace", "Breakfast"],
    image: "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1100&q=85"
  },
  {
    id: "casa",
    name: "Casa Maré",
    location: "Lisbon, Portugal",
    search: "lisbon portugal alfama city",
    type: "deluxe",
    room: "Deluxe king room",
    price: 186,
    rating: "4.86",
    reviews: "94 stays",
    tag: "City, at your pace",
    description: "A sunlit townhouse stay with tiled details, a leafy courtyard, and the city just around the corner.",
    amenities: ["Courtyard", "Walkable", "Coffee bar"],
    image: "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1100&q=85"
  },
  {
    id: "mori",
    name: "Mori House",
    location: "Kyoto, Japan",
    search: "kyoto japan gion old town",
    type: "standard",
    room: "Quiet standard room",
    price: 142,
    rating: "4.97",
    reviews: "76 stays",
    tag: "A quieter corner",
    description: "A calm, wood-and-paper retreat near the old lanes, with soft mornings and thoughtful little rituals.",
    amenities: ["Garden view", "Tea ritual", "Old town"],
    image: "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=1100&q=85"
  }
];

const byId = (id) => document.getElementById(id);
const escapeHTML = (value) => String(value).replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" })[character]);
const params = new URLSearchParams(window.location.search);
const isoDate = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
const plusDays = (n) => { const date = new Date(); date.setDate(date.getDate() + n); return isoDate(date); };
const money = (amount) => new Intl.NumberFormat(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(amount);
let currentResults = [...hotels];
let toastTimer;

function showToast(message) {
  const toast = byId("toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2800);
}

function selectedDates() {
  return { check_in: byId("check-in").value, check_out: byId("check-out").value };
}

async function getAvailability(hotel) {
  const dates = selectedDates();
  const query = new URLSearchParams({ ...dates, room_type: hotel.type });
  const response = await fetch(`/api/availability?${query}`);
  if (!response.ok) throw new Error("Availability could not be checked. Please try again.");
  return response.json();
}

function hotelCard(hotel, availability = null) {
  const available = availability?.available_count;
  const card = document.createElement("article");
  card.className = "hotel-card";
  card.innerHTML = `
    <div class="card-image" role="img" aria-label="${hotel.name}" style="background-image:url('${hotel.image}')">
      <span class="card-badge">${hotel.tag}</span>
    </div>
    <div class="card-body">
      <div class="card-location"><span>⌖</span>${hotel.location}</div>
      <div class="card-title-row"><h3>${hotel.name}</h3><span class="rating"><span>★</span>${hotel.rating}</span></div>
      <p class="card-description">${hotel.description}</p>
      <div class="amenities">${hotel.amenities.map((item) => `<span class="amenity">${item}</span>`).join("")}</div>
      <div class="card-footer"><div><span class="price-label">FROM</span><br /><span class="price">${money(hotel.price)}<small> / night</small></span></div><button class="details-button" type="button">View stay <span>→</span></button></div>
      ${available === null ? "" : `<span class="availability-pill ${available < 1 ? "sold-out" : ""}">${available > 0 ? `${available} ${hotel.type} room${available === 1 ? "" : "s"} available` : "No rooms for these dates"}</span>`}
    </div>`;
  card.querySelector(".card-image").addEventListener("click", (event) => { if (!event.target.closest("button")) openHotel(hotel); });
  card.querySelector(".details-button").addEventListener("click", () => openHotel(hotel));
  return card;
}

async function renderHotels(list = hotels) {
  const grid = byId("hotel-grid");
  grid.replaceChildren();
  byId("empty-state").hidden = list.length > 0;
  byId("result-summary").textContent = list.length === hotels.length && !byId("destination").value.trim() ? "Our little collection" : `${list.length} ${list.length === 1 ? "stay" : "stays"} to explore`;
  byId("results-title").innerHTML = list.length === hotels.length && !byId("destination").value.trim() ? "Somewhere<br /><em>worth going.</em>" : "Your next<br /><em>good pause.</em>";
  list.forEach((hotel) => grid.append(hotelCard(hotel)));
  await Promise.all(list.map(async (hotel) => {
    const card = [...grid.children].find((item) => item.querySelector("h3")?.textContent === hotel.name);
    if (!card) return;
    const status = document.createElement("span");
    status.className = "availability-pill";
    status.textContent = "Checking live availability…";
    card.querySelector(".card-body").append(status);
    try {
      const data = await getAvailability(hotel);
      status.classList.toggle("sold-out", data.available_count < 1);
      status.textContent = data.available_count > 0 ? `${data.available_count} room${data.available_count === 1 ? "" : "s"} available for your dates` : "No rooms for these dates";
    } catch {
      status.classList.add("sold-out");
      status.textContent = "Availability check unavailable";
    }
  }));
}

async function openHotel(hotel) {
  const content = byId("hotel-modal-content");
  const dates = selectedDates();
  content.innerHTML = `<div class="modal-hero" style="background-image:url('${hotel.image}')"></div><div class="modal-content"><p class="eyebrow"><span class="eyebrow-line"></span>${hotel.location}</p><h2 id="modal-title">${hotel.name}</h2><p>${hotel.description}</p><div class="modal-meta"><span>★ ${hotel.rating} · ${hotel.reviews}</span><span>${hotel.room}</span><span>${money(hotel.price)} / night · sample rate</span></div><div class="modal-rate"><div><strong id="modal-availability">Checking room availability…</strong><p class="fine-print">Inventory is live; sample rate is for display only. No payment is collected.</p></div><button class="primary-button" id="reserve-stay" type="button" disabled>Reserve this stay</button></div></div>`;
  byId("hotel-modal").showModal();
  try {
    const availability = await getAvailability(hotel);
    const count = availability.available_count;
    byId("modal-availability").textContent = count ? `${count} ${hotel.type} room${count === 1 ? "" : "s"} available` : "No rooms available for these dates";
    byId("reserve-stay").disabled = count < 1;
    byId("reserve-stay").addEventListener("click", () => openReservationForm(hotel, dates));
  } catch (error) {
    byId("modal-availability").textContent = error.message;
  }
}

function openReservationForm(hotel, dates) {
  byId("hotel-modal").close();
  byId("booking-modal-content").innerHTML = `<div class="form-content"><p class="eyebrow"><span class="eyebrow-line"></span> Make it yours</p><h2 id="booking-title">A few details,<br /><em>then you’re away.</em></h2><p class="form-intro">Your booking will be recorded in the reservation database. This local demo does not collect payment.</p><div class="booking-summary"><strong>${hotel.name} · ${hotel.room}</strong><span>${dates.check_in} to ${dates.check_out} · ${money(hotel.price)} / night sample rate</span></div><form id="reservation-form"><div class="form-grid"><label class="form-label full">Full name<input name="guest_name" autocomplete="name" maxlength="120" required /></label><label class="form-label full">Email address<input name="guest_email" type="email" autocomplete="email" maxlength="254" required /></label></div><p class="form-error" id="reservation-error" role="alert"></p><button class="primary-button" type="submit">Confirm reservation <span>→</span></button></form></div>`;
  byId("booking-modal").showModal();
  byId("reservation-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const submit = form.querySelector("button[type=submit]");
    submit.disabled = true;
    submit.textContent = "Saving reservation…";
    const payload = Object.fromEntries(new FormData(form).entries());
    Object.assign(payload, { room_type: hotel.type, ...dates });
    try {
      const response = await fetch("/api/reservations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error?.message || "Could not save the reservation.");
      showConfirmation(hotel, data, payload);
      await renderHotels(currentResults);
    } catch (error) {
      byId("reservation-error").textContent = error.message;
      submit.disabled = false;
      submit.textContent = "Confirm reservation →";
    }
  });
}

function showConfirmation(hotel, reservation, payload) {
  byId("booking-modal-content").innerHTML = `<div class="form-content"><div class="confirmation-mark">✓</div><p class="eyebrow"><span class="eyebrow-line"></span> All set</p><h2 id="booking-title">Your pause<br /><em>is waiting.</em></h2><p class="form-intro">A reservation has been saved in the live booking database. Keep this reference and the email you used to look it up later.</p><div class="confirmation-box"><div class="confirmation-reference">${escapeHTML(reservation.booking_reference)}</div><div class="confirmation-detail"><span>Stay</span><strong>${escapeHTML(hotel.name)} · room ${escapeHTML(reservation.room_number)}</strong></div><div class="confirmation-detail"><span>Guest</span><strong>${escapeHTML(payload.guest_name)}</strong></div><div class="confirmation-detail"><span>Dates</span><strong>${escapeHTML(reservation.check_in)} — ${escapeHTML(reservation.check_out)}</strong></div><div class="confirmation-detail"><span>Status</span><strong>${escapeHTML(reservation.status)}</strong></div></div><button class="primary-button" id="confirmation-done" type="button">Lovely, thank you</button><p class="fine-print">Sample catalogue rate only. No payment has been taken.</p></div>`;
  byId("confirmation-done").addEventListener("click", () => byId("booking-modal").close());
}

function openLookup() {
  byId("lookup-modal-content").innerHTML = `<div class="form-content"><p class="eyebrow"><span class="eyebrow-line"></span> Your plans</p><h2 id="lookup-title">Find your<br /><em>reservation.</em></h2><p class="form-intro">Enter the booking reference and guest email used when you reserved.</p><form id="lookup-form"><div class="form-grid"><label class="form-label full">Booking reference<input name="reference" placeholder="HB-XXXXXXXXXX" autocapitalize="characters" required /></label><label class="form-label full">Guest email<input name="email" type="email" autocomplete="email" required /></label></div><p class="form-error" id="lookup-error" role="alert"></p><button class="primary-button" type="submit">Find booking <span>→</span></button></form><div id="lookup-result"></div></div>`;
  byId("lookup-modal").showModal();
  byId("lookup-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget).entries());
    const error = byId("lookup-error");
    const result = byId("lookup-result");
    error.textContent = "";
    result.replaceChildren();
    try {
      const response = await fetch("/api/reservations/lookup", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ booking_reference: values.reference.trim().toUpperCase(), guest_email: values.email }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error?.message || "Booking not found.");
      result.innerHTML = `<div class="lookup-result"><div class="confirmation-reference">${escapeHTML(data.booking_reference)}</div><div class="confirmation-detail"><span>Guest</span><strong>${escapeHTML(data.guest_name)}</strong></div><div class="confirmation-detail"><span>Room</span><strong>${escapeHTML(data.room_number)} · ${escapeHTML(data.room_type)}</strong></div><div class="confirmation-detail"><span>Dates</span><strong>${escapeHTML(data.check_in)} — ${escapeHTML(data.check_out)}</strong></div><div class="confirmation-detail"><span>Status</span><strong>${escapeHTML(data.status)}</strong></div></div>`;
    } catch (err) { error.textContent = err.message; }
  });
}

function applySearch() {
  const query = byId("destination").value.trim().toLowerCase();
  currentResults = hotels.filter((hotel) => !query || hotel.search.includes(query) || hotel.name.toLowerCase().includes(query));
  byId("results-title").scrollIntoView({ behavior: "smooth", block: "center" });
  renderHotels(currentResults);
}

function setupDates() {
  const checkIn = byId("check-in");
  const checkOut = byId("check-out");
  checkIn.min = plusDays(0);
  checkOut.min = plusDays(1);
  checkIn.value = params.get("check_in") || plusDays(30);
  checkOut.value = params.get("check_out") || plusDays(32);
  if (params.has("destination")) byId("destination").value = params.get("destination");
  checkIn.addEventListener("change", () => { checkOut.min = plusDays(0); if (checkOut.value <= checkIn.value) { const date = new Date(`${checkIn.value}T12:00:00`); date.setDate(date.getDate() + 1); checkOut.value = isoDate(date); } });
}

document.querySelectorAll(".modal-close").forEach((button) => button.addEventListener("click", () => button.closest("dialog").close()));
byId("search-form").addEventListener("submit", (event) => { event.preventDefault(); if (byId("check-out").value <= byId("check-in").value) { showToast("Check-out needs to be after check-in"); return; } applySearch(); });
byId("open-booking-lookup").addEventListener("click", openLookup);
byId("clear-search").addEventListener("click", () => { byId("destination").value = ""; currentResults = [...hotels]; renderHotels(); });
byId("menu-toggle").addEventListener("click", () => { const open = byId("menu-toggle").getAttribute("aria-expanded") !== "true"; byId("menu-toggle").setAttribute("aria-expanded", String(open)); document.querySelector(".main-nav").classList.toggle("open", open); });
setupDates();
currentResults = params.has("destination") ? hotels.filter((hotel) => hotel.search.includes(params.get("destination").toLowerCase())) : [...hotels];
renderHotels(currentResults);

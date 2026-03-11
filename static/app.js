
var pharmacies = JSON.parse(document.getElementById('pharm-info-json').textContent);
var map = L.map('map').setView([40.1158, 67.8422], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
let markers = [];
let currentUser = null;

function openModal() { document.getElementById('loginModal').style.display = 'flex'; }
function closeModal() { document.getElementById('loginModal').style.display = 'none'; }

async function registerUser() {
    const name = document.getElementById('reg-name').value;
    const phone = document.getElementById('reg-phone').value;
    const role = document.getElementById('reg-role').value;

    if(!name || !phone) return alert("Barcha maydonlarni to'ldiring!");

    navigator.geolocation.getCurrentPosition(async (pos) => {
        try {
            const res = await fetch('/auth/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: name, phone: phone, role: role, 
                    lat: pos.coords.latitude, lon: pos.coords.longitude
                })
            });
            const data = await res.json();
            if(data.status === "success") {
                currentUser = {name, phone, role};
                document.getElementById('user-info').innerHTML = `<div class="bg-blue-800 px-4 py-2 rounded-lg text-xs font-bold uppercase">${name} | ${role}</div>`;
                closeModal();
                updateInterface();
            }
        } catch (e) {
            alert("Server bilan bog'lanishda xato!");
        }
    }, (err) => {
        alert("Joylashuvni aniqlashga ruxsat bering!");
    });
}

function updateInterface() {
    const listTitle = document.getElementById('list-title');
    const searchSection = document.getElementById('search-section');

    const ordersSection = document.getElementById('orders-section');
    if(currentUser.role === 'pharmacy') {
        listTitle.innerText = "📦 Kelgan Buyurtmalar";
        searchSection.style.display = 'none';
        if(ordersSection) ordersSection.style.display = 'none';
        document.getElementById('dynamic-list').innerHTML = `<p class="text-xs text-gray-500 italic py-4 text-center">Yangi buyurtmalar kutilmoqda...</p>`;
    } else if(currentUser.role === 'courier') {
        listTitle.innerText = "🚴 Tayyor Buyurtmalar";
        searchSection.style.display = 'none';
        if(ordersSection) ordersSection.style.display = 'none';
        document.getElementById('dynamic-list').innerHTML = `<p class="text-xs text-gray-500 italic py-4 text-center">Atrofdagi buyurtmalar qidirilmoqda...</p>`;
    } else if(currentUser.role === 'user') {
        search();
        renderCart();
        loadOrders();
        if(ordersSection) ordersSection.style.display = 'block';
    } else {
        search();
        if(ordersSection) ordersSection.style.display = 'none';
    }
}

async function search() {
    const q = document.getElementById('search-input').value;
    try {
        const res = await fetch(`/search?q=${q}`);
        const data = await res.json();
        renderDrugList(data);
    } catch (e) {
        console.error("Qidiruv xatosi:", e);
    }
}

function renderDrugList(data, title = '💊 Jonli Omborxona') {
    let html = '';
    markers.forEach(m => map.removeLayer(m));
    markers = [];

    data.forEach(drug => {
        
        let phoneHtml = '';
        const info = pharmacies[drug.pharmacy];
        if(info && info.phone) {
            phoneHtml = ` <a class="text-blue-600 underline" href="tel:${info.phone}">📞</a>`;
        }
        html += `
                        <div class="p-3 border-b bg-white rounded-lg flex justify-between items-center shadow-sm">
                            <div>
                                <p class="font-bold text-slate-800 text-sm">${drug.name}</p>
                                <p class="text-[10px] text-gray-400"><span class="cursor-pointer underline" onclick="viewPharmacy('${drug.pharmacy.replace("'", "\\'")}')">${drug.pharmacy}</span>${phoneHtml} • ${drug.count} ta bor</p>
                            </div>
                            <div class="text-right">
                                <p class="text-blue-600 font-bold text-xs">${drug.price} so'm</p>
                                <button onclick="orderDrug(${drug.id})" class="bg-green-500 text-white text-[9px] px-3 py-1 rounded-full font-bold hover:bg-green-600 transition">BUYURTMA</button>
                                <button onclick="addToCart({id:${drug.id}, name:'${drug.name.replace("'","\\'")}', pharmacy:'${drug.pharmacy.replace("'","\\'")}'});" class="ml-2 bg-yellow-400 text-white text-[9px] px-3 py-1 rounded-full font-bold hover:bg-yellow-500 transition">Savatcha</button>
                            </div>
                        </div>`;
        let m = L.marker([drug.lat, drug.lon]).addTo(map).bindPopup(`<b>${drug.name}</b><br>${drug.pharmacy}${info && info.phone ? `<br><a href=\"tel:${info.phone}\">📞 ${info.phone}</a>` : ''}`);
        markers.push(m);
    });

    document.getElementById('dynamic-list').innerHTML = html || '<p class="text-center text-gray-400 py-4 text-xs">Dori topilmadi</p>';
    document.getElementById('list-title').innerText = title;
}

async function viewPharmacy(name) {
    try {
        const [resDrugs, resInfo] = await Promise.all([
            fetch(`/pharmacy/${encodeURIComponent(name)}`),
            fetch(`/pharmacy/info/${encodeURIComponent(name)}`)
        ]);
        const data = await resDrugs.json();
        const info = await resInfo.json();
        renderDrugList(data, `📍 ${name} dorixona`);

        const infoDiv = document.getElementById('pharmacy-info');
        let infoHtml = '';
        if(info.phone) {
            infoHtml += `<p>Telefon: <a class="text-blue-600 underline" href="tel:${info.phone}">${info.phone}</a></p>`;
        }
        if(info.address) {
            infoHtml += `<p>Manzil: ${info.address}</p>`;
        }
        if(!infoHtml) {
            infoHtml = '<p class="text-gray-500 italic">Aloqa ma\'lumotі mavjud emas</p>';
        }
        infoDiv.innerHTML = infoHtml;
    } catch (e) {
        console.error('Pharmacy load error', e);
    }
}

let pendingOrderId = null;
let pendingCartIds = null;
let cart = [];


function addToCart(drug) {
    if(!cart.find(d=>d.id===drug.id)) {
        cart.push(drug);
        renderCart();
    }
}
function removeFromCart(id) {
    cart = cart.filter(d=>d.id!==id);
    renderCart();
}
function renderCart() {
    const list = document.getElementById('cart-list');
    if(cart.length===0) {
        list.innerHTML = '<p class="text-gray-500 italic">Savatcha bo`sh</p>';
        return;
    }
    let html='';
    cart.forEach(d=>{
        html += `<div class="flex justify-between items-center">
                    <span>${d.name} (${d.pharmacy})</span>
                    <button onclick="removeFromCart(${d.id})" class="text-red-500 text-xs">x</button>
                 </div>`;
    });
    list.innerHTML = html;
}
function checkoutCart() {
    if(cart.length===0) {
        alert('Savatcha bo`sh');
        return;
    }
    if(!currentUser || currentUser.role!=='user') {
        openModal();
        return;
    }
    pendingCartIds = cart.map(d=>d.id);
    pendingOrderId = null; 
    document.getElementById('contact-phone').value = '';
    document.getElementById('contactModal').style.display = 'flex';
}

function loadOrders() {
    if(!currentUser || currentUser.role!=='user') return;
    fetch(`/orders?customer_phone=${currentUser.phone}`)
        .then(res=>res.json())
        .then(data=>renderOrders(data))
        .catch(e=>console.error('orders load',e));
}

function renderOrders(list) {
    const container = document.getElementById('orders-list');
    if(!list || list.length===0) {
        container.innerHTML = '<p class="text-gray-500 italic">Buyurtma yo`q</p>';
        return;
    }
    let html='';
    list.forEach(o=>{
        html += `<div class="border-b pb-1">
                    <div>${o.drug_name} • ${o.pharmacy}</div>
                    <div class="text-xs text-gray-500">${o.timestamp} • ${o.status}</div>
                 </div>`;
    });
    container.innerHTML = html;
}


async function orderDrug(id) {
    if(!currentUser) {
        
        openModal();
        return;
    }
    if(currentUser.role !== 'user') {
        
        openModal();
        return;
    }
    pendingOrderId = id;
    document.getElementById('contact-phone').value = '';
    document.getElementById('contactModal').style.display = 'flex';
}

function closeContactModal() {
    document.getElementById('contactModal').style.display = 'none';
    pendingOrderId = null;
}

async function submitContact() {
    const contact = document.getElementById('contact-phone').value.trim();
    if(!contact) {
        alert("Iltimos, telefon raqamini kiriting.");
        return;
    }
    closeContactModal();
    try {
        let url;
        if(pendingCartIds && pendingCartIds.length) {
            const ids = pendingCartIds.join(',');
            url = `/order/checkout?customer_phone=${currentUser.phone}&contact_phone=${encodeURIComponent(contact)}&drug_ids=${ids}`;
        } else {
            url = `/order/create/${pendingOrderId}?customer_phone=${currentUser.phone}&contact_phone=${encodeURIComponent(contact)}`;
        }
        const res = await fetch(url, {method: 'POST'});
        const data = await res.json();
        if(data.success) {
            alert("✅ Buyurtma qabul qilindi! Kuryer yolda.");
            
            if(pendingCartIds && pendingCartIds.length) {
                cart = [];
                renderCart();
                pendingCartIds = null;
            }
        } else {
            alert(data.message || "Buyurtma berishda xatolik!");
        }
    } catch (e) {
        alert("Buyurtma berishda xatolik!");
    }
}

async function askBot() {
    if(!currentUser) {
        
        openModal();
        return;
    }
    const input = document.getElementById('chat-input');
    const box = document.getElementById('chat-box');

    if(!input.value) return;

    box.innerHTML += `<div class="text-right"><span class="bg-gray-100 p-2 rounded-lg inline-block text-[10px]">Siz: ${input.value}</span></div>`;
    
    try {
        const res = await fetch(`/ask?text=${encodeURIComponent(input.value)}&phone=${currentUser.phone}`);
        const data = await res.json();
        box.innerHTML += `<div class="text-left"><span class="bg-blue-50 p-2 rounded-lg inline-block text-[10px] text-blue-800"><b>Med-Ai:</b> ${data.reply}</span></div>`;
    } catch (e) {
        box.innerHTML += `<div class="text-left text-red-500 text-[10px]">Tizimda xatolik yuz berdi.</div>`;
    }
    
    input.value = '';
    box.scrollTop = box.scrollHeight;
}

window.onload = () => { search(); renderCart(); loadOrders(); };

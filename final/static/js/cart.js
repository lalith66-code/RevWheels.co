let cart = JSON.parse(localStorage.getItem("cart") || "[]");

function addToCart(name, price){
    cart.push({name, price});
    localStorage.setItem("cart", JSON.stringify(cart));
    alert("Added to cart");
}

function checkout(){
    window.location.href="/checkout";
}

function addToCart(name, price){
  cart.push({name, price});
  localStorage.setItem("cart", JSON.stringify(cart));
  alert("Added to cart");
}

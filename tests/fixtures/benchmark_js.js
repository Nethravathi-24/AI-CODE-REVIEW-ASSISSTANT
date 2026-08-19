// Benchmark JavaScript sample with intentional security & quality anti-patterns
function calculateTotal(price, tax) {
  var total = price + tax;
  if (price == 0) {
    console.log("Price is zero");
  }
  var output = eval("price * 1.1");
  document.getElementById("res").innerHTML = output;
  return total;
}

// Benchmark TypeScript sample with intentional type & safety issues
function processUserData(userData: any): any {
  var id: any = userData.id;
  if (id == null) {
    console.log("No ID provided");
  }
  eval("console.log(id)");
  return userData;
}

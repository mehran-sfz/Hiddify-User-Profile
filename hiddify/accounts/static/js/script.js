document.addEventListener("DOMContentLoaded", function () {
  // تمام المان‌های alert را که مخفی هستند پیدا کن
  const alertBoxes = document.querySelectorAll(".popup-alert.d-none");

  // مدت زمانی که هر پیام نمایش داده می‌شود (5 ثانیه)
  const displayDuration = 5000;
  
  // فاصله زمانی بین نمایش هر پیام (مثلاً دو ثانیه)
  const staggerDelay = 2000;

  // به ازای هر alert یک عملیات زمان‌بندی شده انجام بده
  alertBoxes.forEach((alertBox, index) => {
    
    // محاسبه تاخیر برای نمایش این پیام بر اساس ترتیب آن
    // پیام اول: 0 * 500 = 0 میلی‌ثانیه تاخیر
    // پیام دوم: 1 * 500 = 500 میلی‌ثانیه تاخیر
    // و الی آخر...
    const showDelay = index * staggerDelay;

    // یک تایمر برای نمایش پیام تنظیم کن
    setTimeout(() => {
      // کلاس d-none را حذف کن تا پیام با افکت fade نمایش داده شود
      alertBox.classList.remove("d-none");

      // حالا که پیام نمایش داده شد، یک تایمر دیگر برای بستن آن تنظیم کن
      setTimeout(() => {
        // از API خود بوت‌استرپ برای بستن استفاده کن تا افکت fade-out اجرا شود
        const bsAlert = new bootstrap.Alert(alertBox);
        if (bsAlert) {
          bsAlert.close();
        }
      }, displayDuration); // این تایمر ۲ ثانیه بعد از نمایش، اجرا می‌شود

    }, showDelay); // این تایمر با تاخیر محاسبه‌شده اجرا می‌شود
  });
});

// Function to copy the link to clipboard
function copyLinkToClipboard(link) {
  // Create a temporary input element to hold the link
  const tempInput = document.createElement("input");
  tempInput.value = link;
  document.body.appendChild(tempInput);

  // Select the link and copy it to clipboard
  tempInput.select();
  document.execCommand("copy");

  // Remove the temporary input element
  document.body.removeChild(tempInput);

  // Notify the user
  alert("کپی شد: " + link);
}

// Attach event listeners to all images with QR codes
document.querySelectorAll('img[id^="qrCodeImage_"]').forEach(function (img) {
  img.addEventListener("click", function () {
    // Get the link stored in the data-link attribute
    const link = this.getAttribute("data-link");

    // Copy the link to clipboard
    copyLinkToClipboard(link);
  });
});
document.querySelectorAll('a[id^="invite_code"]').forEach(function (a) {
  a.addEventListener("click", function () {
    const link = this.getAttribute("invite-code");

    // Copy the link to clipboard
    copyLinkToClipboard(link);
  });
});

// Popover Script
const popoverTriggerList = document.querySelectorAll(
  '[data-bs-toggle="popover"]'
);
const popoverList = [...popoverTriggerList].map(
  (popoverTriggerEl) => new bootstrap.Popover(popoverTriggerEl)
);

function confirmDelete() {
  if (confirm("آیا از حذف سفارش اطمینان دارید؟")) {
    document
      .querySelector(
        'form[action="{% url "delete_order" config.last_order.id %}"]'
      )
      .submit();
  }
}

function toggleEditForm() {
  const editForm = document.getElementById("editForm");
  if (editForm.style.display === "none") {
    editForm.style.display = "block";
  } else {
    editForm.style.display = "none";
  }
}


// Function to show the payment form for a specific card
// This function hides the default view and shows the payment form for the specified card ID
function showPaymentForm(cardId) {
  document.getElementById('defaultView_' + cardId).style.display = 'none';
  document.getElementById('paymentFormView_' + cardId).style.display = 'block';
}

function cancelPaymentForm(cardId) {
  document.getElementById('paymentFormView_' + cardId).style.display = 'none';  // Hide the payment form
  document.getElementById('defaultView_' + cardId).style.display = 'block';     // Show the default view
  document.getElementById('qrCodeSection_' + cardId).style.display = 'block';   // Show the QR code section again
}

function togglePaymentForm(counter) {
  const paymentForm = document.getElementById(`paymentFormView_${counter}`);
  const defaultView = document.getElementById(`defaultView_${counter}`);

  if (!paymentForm || !defaultView) {
    console.error("One or more elements not found!");
    return;
  }

  // بررسی کنید که آیا فرم پرداخت کلاس d-none را دارد (یعنی مخفی است)
  if (paymentForm.classList.contains("d-none")) {
    // اگر مخفی است، آن را نمایش بده و نمای پیش‌فرض را مخفی کن
    paymentForm.classList.remove("d-none");
    defaultView.classList.add("d-none");
  } else {
    // در غیر این صورت (یعنی قابل مشاهده است)، آن را مخفی کن و نمای پیش‌فرض را نمایش بده
    paymentForm.classList.add("d-none");
    defaultView.classList.remove("d-none");
  }
}

function cancelPaymentForm(counter) {
  const paymentForm = document.getElementById(`paymentFormView_${counter}`);
  const defaultView = document.getElementById(`defaultView_${counter}`);
  paymentForm.style.display = "none";
  defaultView.style.display = "block";
}


// JavaScript to toggle payment details visibility
document.addEventListener('DOMContentLoaded', function () {
  // Select all toggle buttons
  const toggleButtons = document.querySelectorAll('.toggle-details');
  
  // Add click event listeners to each button
  toggleButtons.forEach(function (button) {
      button.addEventListener('click', function () {
          // Get the target payment details row
          const target = document.querySelector(button.getAttribute('data-target'));
          
          // Toggle the visibility of the payment details row
          if (target.style.display === 'none' || target.style.display === '') {
              target.style.display = 'table-row';  // Show row
          } else {
              target.style.display = 'none';  // Hide row
          }
      });
  });
});


// JavaScript to handle form submission with appropriate value for confirm_payment
document
  .querySelectorAll(".confirm-btn, .reject-btn")
  .forEach(function (button) {
    button.addEventListener("click", function () {
      const form = this.closest("form");
      const hiddenInput = form.querySelector("#confirmPaymentInput");
      hiddenInput.value = this.getAttribute("data-value");
      form.submit();
    });
  });

  
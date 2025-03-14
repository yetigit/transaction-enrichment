(async () => {

  for (let i = 0; i < 3; i++) {
    let year = 2024;
    let month_st = i * 4 + 1;
    let month_en = month_st + 4;

    let year_st = year + Math.floor(month_st / 12);
    let year_en = year + Math.floor(month_en / 12);

    month_st = month_st % 12;
    month_en = month_en % 12;

    if (month_st === 0) month_st = 12;
    if (month_en === 0) month_en = 12;

    let bodyObj = {
      "filters": {
        "date": {
          "start": {
            "year": year_st,
            "month": month_st,
            "day": 1
          },
          "end": {
            "year": year_en,
            "month": month_en,
            "day": 1
          }
        },
        "type": 0
      },
      "maxRows": 500,
      "pagingCursor": null
    };
    
    const response = await fetch("https://apps.seb.se/ssc/payments/accounts/api/accounts/ACCOUNT_NUMBER/transactions/search", {
      "headers": {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "adrum": "isAjax:true",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "organization-id": ORGANIZATION_ID,
        "pragma": "no-cache",
        "priority": "u=1, i",
        "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
      },
      "referrer": "https://apps.seb.se/cps/payments/accounts/",
      "referrerPolicy": "strict-origin-when-cross-origin",
      "body": JSON.stringify(bodyObj),
      "method": "POST",
      "mode": "cors",
      "credentials": "include"
    });
    const data = await response.json();
    console.log(data);

    await new Promise(resolve => setTimeout(resolve, 2000));
  }

})();

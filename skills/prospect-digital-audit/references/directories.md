# Directory listings check

The sheet reports issues out of a fixed 21 directories. Always check exactly these 21, in this order. To change the list, edit this file; the total in `scripts/fill_audit.py` (`DIRECTORY_TOTAL`) must match the list length.

1. Google Business Profile
2. Bing Places
3. Apple Maps (Apple Business Connect)
4. Yelp
5. Facebook
6. Better Business Bureau (bbb.org)
7. Yellow Pages (yellowpages.com)
8. Nextdoor
9. Foursquare
10. MapQuest
11. Manta
12. Superpages
13. Angi
14. Thumbtack
15. Citysearch
16. Hotfrog
17. Brownbook
18. EZlocal
19. MerchantCircle
20. Chamber of Commerce (chamberofcommerce.com)
21. Alignable

## Method

1. Take the reference NAP (name, address, phone) from the prospect's website footer or contact page. If the site has several locations, use the main location from the transcript.
2. For each directory, search `"<business name>" <city> site:<directory domain>`, then open the best match.
3. Classify each directory:
   - **Not Found**: no listing for this business.
   - **Inaccurate**: a listing exists but the name, street address, or phone differs from the reference (ignore abbreviations like St/Street, suite formatting, and punctuation).
   - **Accurate**: everything matches.
4. Record each result with the listing URL under `directories.detail` in `audit.json`.

`Error Rate` = (Inaccurate + Not Found) / 21, computed by the script.

If a directory blocks access or cannot be checked, count it as Not Found only if search engines show no listing either; otherwise mark it unchecked in the detail and note it.

Search-only checks cannot verify the address and phone on Google Business Profile, Bing Places, Apple Maps or Facebook. Mark those Unchecked rather than guessing. Unchecked directories are not counted as errors and the denominator stays 21; say in the notes which directories were Unchecked.

The list is oriented to home-service businesses. Angi and Thumbtack do not apply to professional-services prospects; the checks still run (the denominator stays 21) but a missing listing there should not be raised as a finding.

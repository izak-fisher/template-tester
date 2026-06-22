# Path-test matrix — Expense Pre-Approval templates

Each cell lists the approval tasks that **actually executed** (in activation order) for that profit center + amount.

> Test workflows are started by **isaiah.fisher@pneumatic.app** (user 1, the API key's user). Pneumatic skips any task assigned to the workflow starter (no self-approval), so steps whose approver group includes this user self-skip regardless of amount — marked `ⓢ`. `⚠️` marks a task skipped for no reason found in the API (a real issue to check in the UI).

## Template 20: Pre Approval / Purchase Req (CAPEX Only)

**ⓢ Starter self-skips** (assigned to a group containing the workflow starter isaiah.fisher@pneumatic.app → Pneumatic skips them; they would run for a different initiator, so they can't be validated through this API key):
- #14 Director Approval CMP — under profit center `10080 CMP`
- #64 Director Approval AV-Speciality — under profit center `10120 AV- Speciality`

| Profit Center | Full PC chain | $1000 | $4000 | $10000 |
|---|---|---|---|---|
| 10095 MI Customer Support | [2, 3] | [2, 3] | [2, 3] | [2, 3] |
| 10090 Piano | [4, 5, 6] | [4, 5, 6] | [4, 5, 6] | [4, 5, 6] |
| 10090 Piano - Service | [7, 8, 9] | [7, 8, 9] | [7, 8, 9] | [7, 8, 9] |
| 10100 WSP | [10, 11, 12] | [10, 11, 12] | [10, 11, 12] | [10, 11, 12] |
| 10080 CMP | [13, 14, 15, 16] | [13, 15, 16] ⓢ | [13, 15, 16] ⓢ | [13, 15, 16] ⓢ |
| 10040 CX/DX | [17, 18, 19] | [17, 18, 19] | [17, 18, 19] | [17, 18, 19] |
| 10130 AV Support | [20, 21] | [20, 21] | [20, 21] | [20, 21] |
| 10180 Customer Service | [22, 23, 24] | [22, 23, 24] | [22, 23, 24] | [22, 23, 24] |
| 10181 Toronto DC | [25, 26, 27] | [25, 26, 27] | [25, 26, 27] | [25, 26, 27] |
| 10181 Building - Toronto DC | [28, 29, 30] | [28, 29, 30] | [28, 29, 30] | [28, 29, 30] |
| 10182 Vancouver DC | [31, 32, 33, 34] | [31, 32, 33, 34] | [31, 32, 33, 34] | [31, 32, 33, 34] |
| 10182 Building - Vancouver DC | [35, 36, 37, 38] | [35, 36, 37, 38] | [35, 36, 37, 38] | [35, 36, 37, 38] |
| 10030 Technical Services | [39, 40, 41] | [39, 40, 41] | [39, 40, 41] | [39, 40, 41] |
| 10030 Service DC | [42, 43, 44] | [42, 43, 44] | [42, 43, 44] | [42, 43, 44] |
| 10171 IT | [45, 46, 47] | [45, 46, 47] | [45, 46, 47] | [45, 46, 47] |
| 10160 Finance | [48, 49, 50] | [48, 49, 50] | [48, 49, 50] | [48, 49, 50] |
| 10170 HR | [51, 52, 53] | [51, 52, 53] | [51, 52, 53] | [51, 52, 53] |
| 10070 Music School | [54, 55, 56] | [54, 55, 56] | [54, 55, 56] | [54, 55, 56] |
| 10071 National Education | [57, 58, 59, 60] | [57, 58, 59, 60] | [57, 58, 59, 60] | [57, 58, 59, 60] |
| 10150 AV- Mass Channel | [61, 62, 63] | [61, 62, 63] | [61, 62, 63] | [61, 62, 63] |
| 10120 AV- Speciality | [64, 65, 66] | [65, 66] ⓢ | [65, 66] ⓢ | [65, 66] ⓢ |
| 10165 Building - Other(MP) | [67, 68, 69] | [67, 68, 69] | [67, 68, 69] | [67, 68, 69] |
| 10165 Others - Tak | [70] | [70] | [70] | [70] |
| 10165 Others - Alberto / Liaison | [71] | [71] | [71] | [71] |

<details><summary>task number → name</summary>

- #1 Initiate Process
- #2 Vice President Approval MI Customer Support
- #3 President MI Customer Support Approval
- #4 Director Approval Piano
- #5 VP Approval Piano
- #6 President Approval Piano
- #7 Manager Approval Piano - Service
- #8 Director and VP Approval Piano - Service
- #9 President Approval Piano - Service
- #10 Director Approval WSP
- #11 Vice President Approval WSP
- #12 President Approval WSP
- #13 Manager Approval CMP
- #14 Director Approval CMP
- #15 VP Approval CMP
- #16 President Approval CMP
- #17 Manager Approval CX/DX
- #18 VP Approval CX/DX
- #19 President Approval CX/DX
- #20 VP Approval AV Support
- #21 President Approval AV Support
- #22 Controler Approval Customer Service
- #23 VP Approval Customer Service
- #24 President Approval Customer Service
- #25 Manager Approval Toronto DC
- #26 VP Approval Toronto DC
- #27 President Approval Toronto DC
- #28 Manager Approval Building - Toronto DC
- #29 Manager and VP Approval Building Toronto DC
- #30 President Approval Building Toronto DC
- #31 Assistant Manager Approval Vancouver DC
- #32 Manager Approval Vancouver DC
- #33 VP Approval Vancouver DC
- #34 President Approval Vancouver DC
- #35 Assistant Manager Approval Building - Vancouver DC
- #36 Manager and Manager Approval Building - Vancouver DC
- #37 VP Approval Building Vancouver DC
- #38 President Approval Building - Vancouver DC
- #39 Manager Approval Technical Services
- #40 VP Approval Technical Services
- #41 President Approval Technical Services
- #42 Manager Approval Service DC
- #43 VP Approval Service DC
- #44 President Approval Service DC
- #45 Manager Approval IT
- #46 VP Approval IT
- #47 President Approval IT
- #48 Manager Approval Finance
- #49 VP Approval Finance
- #50 President Approval Finance
- #51 Manager Approval HR
- #52 VP Approval HR
- #53 President Approval HR
- #54 Manager Approval Music School
- #55 VP Approval Music School
- #56 President Approval Music School
- #57 Manager Approval National Education
- #58 2nd Manager Approval National Education
- #59 VP Approval National Education
- #60 President Approval National Education
- #61 Manager Approval AV-Mass Channel
- #62 VP Approval AV-Mass Channel
- #63 President Approval AV-Mass Channel
- #64 Director Approval AV-Speciality
- #65 VP Approval AV-Speciality
- #66 President Approval AV-Speciality
- #67 HR Manager Building - Other (MP)
- #68 Vice President Building - Other (MP)
- #69 President Building - Other (MP)
- #70 Vice President - Others - Tak
- #71 President - Alberto /Liaison

</details>

## Template 7: Pre Approval / Purchase Req (Non CAPEX)

**ⓢ Starter self-skips** (assigned to a group containing the workflow starter isaiah.fisher@pneumatic.app → Pneumatic skips them; they would run for a different initiator, so they can't be validated through this API key):
- #14 Director Approval CMP — under profit center `10080 CMP`
- #64 Director Approval AV-Speciality — under profit center `10120 AV- Speciality`

| Profit Center | Full PC chain | $1000 | $4000 | $10000 |
|---|---|---|---|---|
| 10095 MI Customer Support | [2, 3] | [2] | [2] | [2, 3] |
| 10090 Piano | [4, 5, 6] | [4] | [4, 5] | [4, 5, 6] |
| 10090 Piano - Service | [7, 8, 9] | [7] | [7, 8] | [7, 8, 9] |
| 10100 WSP | [10, 11, 12] | [10] | [10, 11] | [10, 11, 12] |
| 10080 CMP | [13, 14, 15, 16] | [13, 15] ⓢ | [13, 15] ⓢ | [13, 15, 16] ⓢ |
| 10040 CX/DX | [17, 18, 19] | [17] | [17, 18] | [17, 18, 19] |
| 10130 AV Support | [20, 21] | [20] | [20] | [20, 21] |
| 10180 Customer Service | [22, 23, 24] | [22] | [22, 23] | [22, 23, 24] |
| 10181 Toronto DC | [25, 26, 27] | [25] | [25, 26] | [25, 26, 27] |
| 10181 Building - Toronto DC | [28, 29, 30] | [28] | [28, 29] | [28, 29, 30] |
| 10182 Vancouver DC | [31, 33, 34] | [31, 33] | [31, 33] | [31, 33, 34] |
| 10182 Building - Vancouver DC | [32, 35, 36, 37, 38] | [32, 35, 36] | [32, 35, 36, 37] | [32, 35, 36, 37, 38] |
| 10030 Technical Services | [39, 40, 41] | [39] | [39, 40] | [39, 40, 41] |
| 10030 Service DC | [42, 43, 44] | [42] | [42, 43] | [42, 43, 44] |
| 10171 IT | [45, 46, 47] | [45] | [45, 46] | [45, 46, 47] |
| 10160 Finance | [48, 49, 50] | [48] | [48, 49] | [48, 49, 50] |
| 10170 HR | [51, 52, 53] | [51] | [51, 52] | [51, 52, 53] |
| 10070 Music School | [54, 55, 56] | [54] | [54, 55] | [54, 55, 56] |
| 10071 National Education | [57, 58, 59, 60] | [57, 59] | [57, 58, 59] | [57, 58, 59, 60] |
| 10150 AV- Mass Channel | [61, 62, 63] | [61] | [61, 62] | [61, 62, 63] |
| 10120 AV- Speciality | [64, 65, 66] | [65] ⓢ | [65] ⓢ | [65, 66] ⓢ |
| 10165 Building - Other(MP) | [67, 68, 69] | [67] | [67, 68] | [67, 68, 69] |
| 10165 Others - Tak | [70] | [70] | [70] | [70] |
| 10165 Others - Alberto / Liaison | [71] | [71] | [71] | [71] |

<details><summary>task number → name</summary>

- #1 Initiate Process
- #2 Vice President Approval MI Customer Support
- #3 President MI Customer Support Approval
- #4 Director Approval Piano
- #5 VP Approval Piano
- #6 President Approval Piano
- #7 Manager Approval Piano - Service
- #8 Director and VP Approval Piano - Service
- #9 President Approval Piano - Service
- #10 Director Approval WSP
- #11 Vice President Approval WSP
- #12 President Approval WSP
- #13 Manager Approval CMP
- #14 Director Approval CMP
- #15 VP Approval CMP
- #16 President Approval CMP
- #17 Manager Approval CX/DX
- #18 VP Approval CX/DX
- #19 President Approval CX/DX
- #20 VP Approval AV Support
- #21 President Approval AV Support
- #22 Controler Approval Customer Service
- #23 VP Approval Customer Service
- #24 President Approval Customer Service
- #25 Manager Approval Toronto DC
- #26 VP Approval Toronto DC
- #27 President Approval Toronto DC
- #28 Manager Approval Building - Toronto DC
- #29 Manager and VP Approval Building - Toronto DC
- #30 President Approval Building Toronto DC
- #31 Assistant Manager Approval Vancouver DC
- #32 Manager Approval Vancouver DC
- #33 VP Approval Vancouver DC
- #34 President Approval Vancouver DC
- #35 Assistant Manager Approval Building - Vancouver DC
- #36 Manager and Manager Approval Building - Vancouver DC
- #37 VP Approval Building Vancouver DC
- #38 President Approval Building Vancouver DC
- #39 Manager Approval Technical Services
- #40 VP Approval Technical Services
- #41 President Approval Technical Services
- #42 Manager Approval Service DC
- #43 VP Approval Service DC
- #44 President Approval Service DC
- #45 Manager Approval IT
- #46 VP Approval IT
- #47 President Approval IT
- #48 Manager Approval Finance
- #49 VP Approval Finance
- #50 President Approval Finance
- #51 Manager Approval HR
- #52 VP Approval HR
- #53 President Approval HR
- #54 Manager Approval Music School
- #55 VP Approval Music School
- #56 President Approval Music School
- #57 Manager Approval National Education
- #58 Second Manager Approval National Education
- #59 VP Approval National Education
- #60 President Approval National Education
- #61 Manager Approval AV-Mass Channel
- #62 VP Approval AV-Mass Channel
- #63 President Approval AV-Mass Channel
- #64 Director Approval AV-Speciality
- #65 VP Approval AV-Speciality
- #66 President Approval AV-Speciality
- #67 HR Manager Building - Other (MP)
- #68 Vice President Building - Other (MP)
- #69 President Building - Other (MP)
- #70 Vice President - Others - Tak
- #71 President - Alberto /Liaison

</details>

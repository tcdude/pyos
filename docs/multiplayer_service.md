# Specification of the multiplayer service protocol

## Message structure

Each message is initiated by the client running in the foreground app. A message
is prefixed with a single `unsigned char`, indicating the type of request.
Behind the request byte a variable length payload can be appended, depending
on the request type. The separator for multiple values is three `null` bytes.

The service will respond with a single `unsigned char` upon completion
indicating success of the operation *(0 = success, 1+ = failed)*, thus signaling
that data is available for reading (success) or an error code to be handled
/ displayed in the foreground app.

----

## Requests

| REQ | Description | Payload |
| :---: | --- | --- |
| 0   | **Create New Account** | Username, Password |
| 1   | **Change Username** | New Username |
| 2   | **Change Password** | New password |
| 3   | **Synchronize Relationships** | *None* |
| 4   | **Reply Friend Request** | User ID, Decison |
| 5   | **Unblock User** | User ID, Decison |
| 6   | **Block User** | User ID |
| 7   | **Remove Friend** | User ID |
| 8   | **Set Draw Count Preference** | Preference |
| 9   | **Update Daily Deal Best Scores** | *None* |
| 10  | **Update Challenge Leaderboard** | Rank Range |
| 11  | **Update User Ranking** | *None* |
| 12  | **Submit Day Deal Score** | Draw, Day Offset, Result |
| 13  | **Start Challenge** | User ID, Rounds |
| 14  | **Synchronize Challenges** | *None* |
| 15  | **Submit Challenge Round Result** | Challenge ID, Round#, Result |
| 16  | **Start Friend Request** | Username |
| 17  | **Update Challenge Stats** | User ID |
| 18  | **Update Specific User** | User ID |
| 19  | **Reject Challenge** | Challenge ID |
| 20  | **Accept Challenge** | Challenge ID, Draw, Score |
| 255 | **Stop Service** | *None* |


# Quản Lý Thiết Bị Làm Việc

Mỗi người nhận một máy Mac mới khi gia nhập 37signals. Chúng tôi quản lý và bảo mật các thiết bị này tập trung với Kandji, giúp giảm rủi ro sự cố bảo mật. Kandji áp dụng cấu hình tiêu chuẩn cho mọi thiết bị (ví dụ: bật mã hóa đĩa, tường lửa, quy tắc mật khẩu), cài đặt ứng dụng thiết yếu (ví dụ: EncryptMe), và đảm bảo các ứng dụng có cập nhật bảo mật mới nhất. Kandji cũng cho phép chúng tôi xóa thiết bị từ xa nếu bị mất, hoặc khi nhân viên rời công ty.

Chúng tôi chủ yếu sử dụng macOS và Linux tại 37signals để phát triển và hỗ trợ ứng dụng.

Với macOS, chúng tôi quản lý và bảo mật tập trung với Kandji. Kandji áp dụng cấu hình tiêu chuẩn cho mọi thiết bị (ví dụ: bật mã hóa đĩa, tường lửa, quy tắc mật khẩu), cài đặt ứng dụng thiết yếu, và đảm bảo các ứng dụng có cập nhật bảo mật mới nhất. (Điều này không có nghĩa là bạn đang bị giám sát hoặc theo dõi! Kandji là hệ thống quản lý cấu hình, không phải panopticon.)

Với Linux, chúng tôi chạy Omarchy, đã tích hợp cấu hình tiêu chuẩn cần thiết (mã hóa toàn đĩa, tường lửa, v.v.). Ở đây chúng tôi dựa vào 1password để cung cấp việc onboarding/offboarding nhân viên truy cập thông tin đăng nhập và VPN Tailscale để kiểm soát truy cập vào hệ thống nội bộ.

## Truy Cập Mã Nguồn Và Bí Mật

Biết thiết bị của chúng tôi an toàn và bảo mật cho phép chúng tôi giao phó máy tính công việc truy cập vào các hệ thống nhạy cảm như Queenbee, VPN nội bộ và máy chủ từ xa. Điều này có nghĩa là cài đặt VPN, tải mã 37signals, và lưu trữ bí mật chỉ được thực hiện trên thiết bị công việc, không phải thiết bị cá nhân.

Vui lòng không lưu dữ liệu cá nhân trên máy tính do 37signals cấp. Bạn nên duy trì một máy tính cá nhân riêng nếu cần máy tính tại nhà. Công ty bảo lưu quyền, và có thể bị yêu cầu, thu giữ máy tính hoặc dữ liệu của bạn bất cứ lúc nào để đáp ứng lệnh triệu tập, vụ kiện, hoặc sự cố bảo mật.

## Thiết Bị Di Động Và Windows

Các thiết bị chạy Android, iOS/iPadOS và Windows hiện không được quản lý. Bạn có thể cài đặt ứng dụng BC4 và HEY trên các thiết bị này để truy cập dự án và email công việc, nhưng vì chúng không được quản lý – và do đó 'không tin cậy' – không được phép lưu trữ mã 37signals hoặc bí mật trên chúng. Nếu bạn đang viết mã hoặc truy cập hệ thống bảo mật, bạn nên làm trên Mac được quản lý bởi Kandji hoặc máy Linux Omarchy.

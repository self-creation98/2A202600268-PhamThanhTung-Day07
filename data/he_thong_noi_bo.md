# Hệ Thống Nội Bộ Của Chúng Tôi

Ngoài các ứng dụng hướng đến khách hàng, như các phiên bản khác nhau của Basecamp, chúng tôi có một số hệ thống nội bộ giúp chúng tôi hỗ trợ, báo cáo và vận hành công ty.

## Queenbee

Queenbee là hệ thống hóa đơn, kế toán và nhận dạng của chúng tôi. Tại đây bạn có thể tra cứu bất kỳ tài khoản khách hàng nào, xem liệu họ có được tặng, hoàn tiền hóa đơn, hoặc thậm chí đăng nhập với tư cách khách hàng.

Đó là một lượng quyền lực rất lớn và chúng tôi rất nghiêm túc trong việc sử dụng nó. Chúng tôi chỉ đăng nhập với tư cách khách hàng sau khi được cho phép rõ ràng, không bao giờ chủ động. Khách hàng kỳ vọng thông tin của họ là bí mật, ngay cả với chúng tôi, và chúng tôi dự định tôn trọng kỳ vọng đó mọi lúc.

## Sentry

Chúng tôi theo dõi lỗi lập trình trên Sentry. Khi khách hàng gặp màn hình "Rất tiếc, đã xảy ra sự cố!", điều đó có nghĩa là sẽ có một mục trong Sentry giải thích cho lập trình viên tại sao họ thấy màn hình đó. Kiểm soát và giám sát lỗi chủ yếu là trách nhiệm của SIP và Jim qua lịch trực.

## Grafana

Chúng tôi giám sát hệ thống và sức khỏe của chúng qua Grafana. Tại đây bạn sẽ tìm thấy bảng điều khiển và quy tắc cảnh báo. Đây là công cụ chính để chẩn đoán vấn đề hiệu suất, sự cố ngừng hoạt động, và bất kỳ hình thức nào khác của cái nhìn vận hành.

## Dash

Dash là trung tâm chính cho mọi thứ liên quan đến ghi log (như tìm lý do request chậm hoặc email đã được gửi chưa), báo cáo (mọi thứ từ số case hỗ trợ đã xử lý đến phân chia thiết bị truy cập Basecamp), sức khỏe ứng dụng (thời gian phản hồi, lỗi hàng đợi công việc, v.v.).

## Omarchy

Omarchy là bản phân phối Linux mới mà mọi người trong Ops, SIP, và lập trình viên Ruby trên Product đang chuyển sang. Chúng tôi phát triển nó nội bộ và tiếp tục dẫn dắt phát triển.

## Kandji

Kandji là cách chúng tôi đảm bảo tất cả laptop Mac công việc được cấu hình an toàn và chạy cập nhật phần mềm mới nhất. Nó giúp giảm rủi ro sự cố bảo mật.

## Shipshape

Shipshape là công cụ nội bộ ban đầu để đảm bảo laptop Mac công việc an toàn và bảo mật. Chúng tôi vẫn chạy nó, nhưng đang dần được thay thế bởi Kandji.

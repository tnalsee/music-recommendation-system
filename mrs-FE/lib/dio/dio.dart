import 'package:dio/dio.dart';

class Client {
  Dio init() {
   BaseOptions options = BaseOptions(baseUrl: "127.0.0.1:8000/api/upload"); //포트번호  변경
   final dio = Dio(options);
   dio.interceptors.add(CustomInterceptor());

   return dio;
  }
}

class CustomInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    print("[REQ] ${options.method} + ${options.uri}");
    super.onRequest(options, handler);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    print("[RES] ${response.data}");
    super.onResponse(response, handler);
  }
}
import axios from "axios";

jest.mock("axios");

export const mockedAxios = axios as unknown as jest.Mock;

export interface RecordedCall {
  method: string;
  url: string;
  headers: Record<string, string>;
  params?: Record<string, unknown>;
  data?: unknown;
}

/** Queue a successful `{ success, data }` envelope response. */
export function mockData(data: unknown, status = 200): void {
  mockedAxios.mockResolvedValueOnce({ status, data: { success: true, data } });
}

/** Queue a raw response body with an explicit status. */
export function mockRaw(body: unknown, status = 200): void {
  mockedAxios.mockResolvedValueOnce({ status, data: body });
}

/** The config object passed to the most recent axios call. */
export function lastCall(): RecordedCall {
  const calls = mockedAxios.mock.calls;
  return calls[calls.length - 1][0] as RecordedCall;
}

export function resetAxios(): void {
  mockedAxios.mockReset();
}

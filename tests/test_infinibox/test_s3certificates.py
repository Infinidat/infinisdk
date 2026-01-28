import responses
import tempfile

from tests.test_infinibox.mock_infinibox.mock_s3certificates import GET_CERTIFICATES


def test_get_certificates(mocked_infinibox_api, mocked_infinibox):
    add_mock, _ = mocked_infinibox_api
    add_mock(
        method=responses.GET,
        url="http://ibox3441:80/api/rest/system/s3_certificates",
        json=GET_CERTIFICATES,
    )

    certificate = mocked_infinibox.s3_certificates.get_certificates().to_list()[0]
    assert certificate.get("id") == "httpd"


def test_generate_self_signed(mocked_infinibox_api, mocked_infinibox):
    add_mock, _ = mocked_infinibox_api

    add_mock(
        method=responses.POST,
        url="http://ibox3441:80/api/rest/system/s3_certificates/generate_csr",
        json=GET_CERTIFICATES,
    )

    certificate = mocked_infinibox.s3_certificates.generate_self_signed()[0]
    assert certificate.get("id") == "httpd"


def test_upload_csr(mocked_infinibox_api, mocked_infinibox):
    add_mock, _ = mocked_infinibox_api
    add_mock(
        method=responses.POST,
        url="http://ibox3441:80/api/rest/system/s3_certificates/upload_csr",
        json=GET_CERTIFICATES,
    )

    with tempfile.NamedTemporaryFile(suffix=".csr") as temp_csr:
        temp_csr.write(b"mocked csr data")
        temp_csr.flush()

        certificate = mocked_infinibox.s3_certificates.upload_csr(temp_csr.name)[0]
        assert certificate.get("id") == "httpd"


def test_upload_pem(mocked_infinibox_api, mocked_infinibox):
    add_mock, _ = mocked_infinibox_api

    add_mock(
        method=responses.POST,
        url="http://ibox3441:80/api/rest/system/s3_certificates",
        json=GET_CERTIFICATES,
    )

    with tempfile.NamedTemporaryFile(suffix=".pem") as temp_pem:
        temp_pem.write(b"mocked pem data")
        temp_pem.flush()

        certificate = mocked_infinibox.s3_certificates.upload_pem(temp_pem.name)[0]
        assert certificate.get("id") == "httpd"

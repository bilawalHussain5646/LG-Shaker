import React, { useState, useContext, useEffect } from "react";
import { AuthContext } from "../context";
import download from "downloadjs"; // Import download.js
import html2canvas from "html2canvas";

const Dashboard = () => {
  const [tableRows, setTableRows] = useState([]);
  const [state, setState] = useState({
    searchtext: "",
  });

  const [prev_num, setprev_num] = useState("");
  const [has_prev, sethas_prev] = useState("");
  const [next_num, setnext_num] = useState("");
  const [has_next, sethas_next] = useState("");
  const [pagination_page, setpagination_page] = useState("");
  const [paginat, setpaginat] = useState([]);

  const { base_url, isLoggedIn, setIsLoggedIn, setUser, user } =
    useContext(AuthContext);
  //   console.log(user);
  useEffect(() => {
    const token_verification = async () => {
      let token = sessionStorage.getItem("token"); // get token
      if (!token || token === undefined || token === "") {
        setUser("");
        setIsLoggedIn(false);
      } else {
        // else send a request to the route and validate whether the token is valid or not
        let result = await fetch(`${base_url}/user-info`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }).catch((err) => {
          //   console.log(err);
        });

        if (result && result.ok) {
          let data = await result.json();
          setIsLoggedIn(true);
          setUser(data);
          //   page_number = page;
          //   console.log(window.location.search);
          const urlParams = new URLSearchParams(window.location.search);
          const myParam = urlParams.get("page");
          let data_table = await fetch(`${base_url}/entries?page=${myParam}`, {
            method: "GET",
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }).catch((err) => {
            // console.log(err);
          });
          if (data_table && data_table.ok) {
            let table_records = await data_table.json();
            setTableRows(table_records.data);
            sethas_next(table_records.has_next);
            sethas_prev(table_records.has_prev);
            setpaginat(table_records.paginat);
            setpagination_page(table_records.pagination_page);
            // console.log(table_records.pagination_page);
            setprev_num(table_records.prev_num);
            setnext_num(table_records.next_num);
            // console.log(table_records.data);
          }
        } else {
          sessionStorage.clear();
          setIsLoggedIn(false);
          setUser("");
        }
      }
    };
    token_verification();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoggedIn]); // for verifying the token and protect login

  const handleLogout = async (event) => {
    event.preventDefault();

    let token = sessionStorage.getItem("token");
    if (!token || token === undefined || token === "") {
      sessionStorage.clear();
      setIsLoggedIn(false);
      setUser("");
    } else {
      await fetch(`${base_url}/logout`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
        .then((res) => {
          sessionStorage.clear();
          setIsLoggedIn(false);
          setUser("");
        })
        .catch((err) => console.log(err));
    }
  };
  const update = (event) => {
    const target = event.currentTarget;

    setState({
      ...state,
      [target.name]: target.type === "checkbox" ? target.checked : target.value,
    });
  };
  const handleDownload = async (event, id) => {
    event.preventDefault();
    window.open(`${base_url}/download/${id}`);
  };
  const handleSearch = async (event) => {
    event.preventDefault();
    let token = sessionStorage.getItem("token");
    if (!token || token === undefined || token === "") {
      sessionStorage.clear();
      setIsLoggedIn(false);
      setUser("");
    } else {
      try {
        let data_table = await fetch(
          `${base_url}/entries?text=${state.searchtext}`,
          {
            method: "GET",
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        ).catch((err) => {
          // console.log(err);
        });
        if (data_table && data_table.ok) {
          let table_records = await data_table.json();
          setTableRows(table_records.data);
          sethas_next(table_records.has_next);
          sethas_prev(table_records.has_prev);
          setpaginat(table_records.paginat);
          setpagination_page(table_records.pagination_page);
          //   console.log(table_records.pagination_page);
          setprev_num(table_records.prev_num);
          setnext_num(table_records.next_num);
          // console.log(table_records.data);
        }
      } catch (err) {
        // console.log(err.status);
      }
    }
  };
  const copyTextToClipboard = () => {
    let text = document.getElementById("view_link").getAttribute("href");
    // console.log(text);
    let full_link = text;
    // Create a new text area element
    const textArea = document.createElement("textarea");

    // Set the text content to the text you want to copy
    textArea.value = full_link;

    // Append the text area to the document
    document.body.appendChild(textArea);

    // Select the text inside the text area
    textArea.select();

    // Execute the "copy" command to copy the selected text to the clipboard
    document.execCommand("copy");

    // Remove the temporary text area
    document.body.removeChild(textArea);
    document
      .getElementById("link_copy_btn")
      .setAttribute("title", "Link copied");
  };
  const copyImageToClipboard = () => {
    html2canvas(document.querySelector("#qr_code_image"), {
      logging: false,
    }).then((canvas) =>
      canvas.toBlob((blob) =>
        navigator.clipboard.write([new ClipboardItem({ "image/png": blob })])
      )
    );
    document
      .getElementById("copy_title_image")
      .setAttribute("title", "Image Copied");
  };
  const open_view_box = async (entry_id) => {
    // console.log(entry_id);

    // Send an AJAX request to fetch the image data
    await fetch(`${base_url}/api/image/${entry_id}`) // Replace with your image API route
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          alert(data.error);
        } else {
          // Set the retrieved image data as the src attribute of the <img> tag
          // console.log(data)
          document.getElementById("qr_code_image").src =
            "data:image/jpeg;base64," + data.image_data; // Adjust the MIME type accordingly
        }
      })
      .catch((error) => {
        console.error("Error fetching image:", error);
      });

    document.getElementById("entry_id_view").value = entry_id;
    // let entry_id = entry_id.toString();
    // entry_id = "{{ entry_id }}";  // Ensure entry_id is a valid JavaScript variable.
    var url_ = `${base_url}/download/${entry_id}`;
    document.getElementById("view_link").setAttribute("href", url_);
    document.getElementById("myModal_view").style.display = "block";
  };
  function close_view_box() {
    document.getElementById("myModal_view").style.display = "none";
    document.getElementById("entry_id_view").value = "";
    document.getElementById("view_link").setAttribute("href", "");
    document.getElementById("qr_code_image").src = ""; // Adjust the MIME type accordingly
  }
  return (
    <div className="p-3">
      <div className="row">
        <div className="col text-center" style={{ paddingLeft: "13rem" }}>
          <h3>LG Shaker Co. Lab.</h3>
        </div>
        <div className="col-auto d-flex justify-content-end pe-4 text-dark">
          <i
            className="fa fa-user-circle fa-2x"
            aria-hidden="true"
            style={{ color: "gray" }}
          ></i>
          <span className="px-2 pt-1">{user ? user.user.email : ""}</span>
        </div>
      </div>
      <div className="row m-0">
        <div className="col">
          <h4 className="text-center text-dark" style={{ paddingLeft: "5rem" }}>
            Stock List
          </h4>
        </div>
        <div className="col-auto d-flex justify-content-end ">
          <button
            type="button"
            className="btn btn-light btn-block text-danger shadow"
            style={{ width: "auto" }}
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </div>
      <div className="row"></div>
      <div className="row m-0">
        <div className="col d-flex justify-content-start">
          <div className="col-auto">
            <div>
              <input
                className="form-control"
                type="text"
                name="searchtext"
                id="searchtext"
                onChange={update}
                placeholder="Model name"
              />
            </div>
          </div>

          <button
            className="btn btn-danger btn-block ms-2"
            style={{ width: "auto" }}
            onClick={handleSearch}
          >
            <i className="fa fa-search" aria-hidden="true"></i> Search
          </button>
        </div>
      </div>
      <div className="table-responsive" style={{ padding: "0 15px" }}>
        <table className="table" style={{ margin: "30px 0px 60px 0px" }}>
          <thead className="thead-dark">
            <tr>
              <th scope="col">S.NO</th>
              <th scope="col">Model Name</th>
              <th scope="col">Report Number</th>
              <th scope="col">Issue Date</th>
              <th scope="col">Contact Number</th>
              <th scope="col">Country of Origin</th>
              <th scope="col">Lab Name</th>
              <th scope="col">Manufacturer Name</th>
              <th scope="col">View</th>
            </tr>
          </thead>
          <tbody>
            {tableRows.map((rec, index) => {
              return (
                <tr key={index}>
                  <th scope="row">
                    {(pagination_page - 1) * 10 + (index + 1)}
                  </th>
                  <td>{rec.model_name}</td>
                  <td>{rec.report_number}</td>

                  <td style={{ textTransform: "capitalize" }}>
                    {new Date(rec.issue_date).toLocaleString("en-ZA", {
                      day: "2-digit",
                    }) +
                      "-" +
                      new Date(rec.issue_date).toLocaleString("en-ZA", {
                        month: "short",
                      }) +
                      "-" +
                      new Date(rec.issue_date).toLocaleString("en-ZA", {
                        year: "2-digit",
                      })}
                  </td>
                  <td>{rec.contact_number}</td>
                  <td>{rec.country_of_origin}</td>
                  <td>{rec.lab_name}</td>
                  <td>{rec.manufacturer_name}</td>
                  <td>
                    {rec.pdf_file === null ? (
                      <button
                        className="bg-transparent border-0 text-danger text-start p-0"
                        disabled
                      >
                        Missing
                      </button>
                    ) : (
                      <button
                        className="btn p-0"
                        data-bs-toggle="modal"
                        data-bs-target="#myModal_view"
                        onClick={() => open_view_box(rec.id)}
                      >
                        <i
                          className="fa fa-eye fa-2x"
                          style={{ color: "#a50034" }}
                          aria-hidden="true"
                        ></i>
                      </button>
                      // <button
                      //   type="button"
                      //   onClick={(e) => handleDownload(e, rec.id)}
                      //   className="bg-transparent border-0 text-dark text-decoration-underline text-start p-0"
                      // >
                      //   Click to Download
                      // </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="my-5">
        <ul
          className="pagination justify-content-center"
          style={{
            maxWidth: "100% !important",
            overflow: "inherit !important",
            display: "flex !important",
          }}
        >
          {has_prev !== "" && has_prev === true ? (
            <li className="page-item">
              <a
                className="page-link text-dark"
                href={`?page=${prev_num}`}
                tabIndex="-1"
              >
                Previous
              </a>
            </li>
          ) : (
            <li className="page-item disabled">
              <a className="page-link" href={`?page=${prev_num}`} tabIndex="-1">
                Previous
              </a>
            </li>
          )}{" "}
          {paginat.map((rec, index) => {
            return pagination_page !== rec ? (
              rec == null ? (
                <li className="page-item disabled" keys={index}>
                  <a className="page-link" href="#">
                    ...
                  </a>
                </li>
              ) : (
                <li className="page-item" keys={index}>
                  <a className="page-link text-dark" href={`?page=${rec}`}>
                    {rec}
                  </a>
                </li>
              )
            ) : (
              <li className="page-item active " keys={index}>
                <a className="page-link">{rec}</a>
              </li>
            );
          })}
          {has_next !== "" && has_next === true ? (
            <li className="page-item">
              <a className="page-link text-dark" href={`?page=${next_num}`}>
                Next
              </a>
            </li>
          ) : (
            <li className="page-item disabled">
              <a className="page-link" href="#">
                Next
              </a>
            </li>
          )}
        </ul>
      </div>

      <div className="modal" id="myModal_view">
        <div className="modal-dialog">
          <div className="modal-content">
            <div className="modal-header d-flex justify-content-center">
              <h4 className="modal-title text-dark">View Report</h4>
            </div>
            <input type="text" name="id" id="entry_id_view" readOnly hidden />

            <div className="form-group d-flex justify-content-center">
              <div className="row m-0">
                <div className="col-6 d-flex justify-content-end">
                  <img id="qr_code_image" src="" alt="qr_code" width="150px" />
                </div>
                <div className="col p-4 px-2  d-flex align-content-center">
                  <div className="row m-0  d-flex align-content-center">
                    <div className="col p-0">Scan the Code</div>

                    <div className="col-4">
                      <button
                        id="copy_title_image"
                        title="Copy to clipboard"
                        onClick={() => copyImageToClipboard()}
                        style={{
                          marginLeft: "5px",
                          fontSize: "14px",
                          backgroundColor: "transparent",
                          color: "#1882ba",
                          border: "1px solid #f0eeee",
                        }}
                      >
                        <i className="fa fa-copy"></i>
                      </button>
                    </div>
                    <div
                      className="col-8 p-0"
                      style={{ display: "flex", textWrap: "nowrap" }}
                    >
                      <a
                        id="view_link"
                        href=""
                        target="_blank"
                        className="bg-transparent border-0 text-danger text-decoration-underline text-start p-0"
                      >
                        Click here to view
                      </a>
                    </div>
                    <div className="col-4">
                      <button
                        id="link_copy_btn"
                        title="Copy link"
                        onClick={() => copyTextToClipboard()}
                        style={{
                          marginLeft: "5px",
                          fontSize: "14px",
                          backgroundColor: "transparent",
                          color: "#1882ba",
                          border: "1px solid #f0eeee",
                        }}
                      >
                        <i className="fa fa-copy"></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-light"
                data-bs-dismiss="modal"
                onClick={() => close_view_box()}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
      {/* </div> */}
    </div>
  );
};

export default Dashboard;

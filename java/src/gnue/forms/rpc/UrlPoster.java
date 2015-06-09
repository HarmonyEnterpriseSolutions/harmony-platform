/*=========================================================================

  Program:   Sula 0.7
  Source:	 $Source: C:/HOME/cvs/wm/java/src/gnue/forms/rpc/UrlPoster.java,v $
  Date:		 $Date: 2012/03/01 11:44:45 $
  Version:   $Revision: 1.6 $

=========================================================================*/

/*
 * TextClient.java
 *
 * Created on November 19, 2002, 2:40 PM
 */

package gnue.forms.rpc;

import java.io.*;
import java.net.*;
import java.lang.*;
import java.util.*;

/**
 *
 * @author  oleg
 * @version $Revision: 1.6 $
 */
public class UrlPoster {
	
	public static class HttpException extends IOException {
		public HttpException(String message) {
			super(message);
		}
	}

	private static final int RETRY_COUNT = 5;

	/** Holds value of property encoding. */
	private String encoding = "UTF8";

	/** Holds value of property url. */
	private URL url;

	/** Holds value of property url. */
	private String[][] headers;

	public UrlPoster(URL url, String[][] headers) {
		this.url = url;
		this.headers = headers;
	}

	public UrlPoster(URL url, String[][] headers, String encoding) {
		this(url, headers);
		this.encoding = encoding;
	}

	public Reader openTextStream(String request) throws IOException {
		return new InputStreamReader(openBinaryStream(request), encoding);
	}

	public InputStream openBinaryStream(String request) throws IOException {
		//System.out.println("Open stream to: " + url + "?" + request);
		int retryCount = RETRY_COUNT;
		OutputStream outStream = null;
		URLConnection con = null;
		while (true) {
			con = url.openConnection();
			con.setDoOutput(true);
			con.setDoInput(true);
			con.setUseCaches(false);
	
			for (int i=0; i<headers.length; i++) {
				con.setRequestProperty(headers[i][0], headers[i][1]);
			}
			
			con.setAllowUserInteraction(false);
	
			//if (monitor != null)
			//	  monitor.setMessage("Sending request...");
	
			try {
				outStream = con.getOutputStream();

				Writer out = new OutputStreamWriter(outStream, encoding);
				out.write(request);
				out.close();
		
				//if (monitor != null)
				//	  monitor.setMessage("Receiving response");
		
				testHeader(con); //Test for errors from server, if so, generate exception
				
				break;
			}
			catch (ConnectException e) {
				if ("Connection timed out".equals(e.getMessage())) {
					if (--retryCount <= 0) {
						throw e;
					}
					//else loop
					System.out.println("+ Retrying connect (Connection timed out)");
					continue;
				}
				else {
					throw e;
				}
			}
			catch (UrlPoster.HttpException e) {
				if ("HTTP error 400".equals(e.getMessage())) {
					if (--retryCount <= 0) {
						throw e;
					}
					//else loop
					System.out.println("+ Retrying connect (HTTP 400)");
					continue;
				}
				else {
					throw e;
				}
			}
		}

		InputStream in = con.getInputStream();

		//if (monitor != null)
		//	  in = new ProgressMonInputStream(monitor, con.getContentLength(), in);

		return in;
	}

	protected void testHeader(URLConnection c) throws IOException {
		String hf = c.getHeaderField(0);
		if (hf != null) {
			StringTokenizer tokenizer = new StringTokenizer(hf);
			String errorCodeStr = null;
			for (int i = 0; i < 2 && tokenizer.hasMoreTokens(); i++)
				errorCodeStr = tokenizer.nextToken();
			int errorCode = Integer.parseInt(errorCodeStr);
			if (errorCode >= 300)
				throw new UrlPoster.HttpException("HTTP error " + errorCode);
		}
		else
			throw new UrlPoster.HttpException("No headers in response");
	}


	/** Getter for property encoding.
	 * @return Value of property encoding.
	 */
	public String getEncoding() {
		return encoding;
	}

	/** Setter for property encoding.
	 * @param encoding New value of property encoding.
	 */
	public void setEncoding(String encoding) {
		this.encoding = encoding;
	}

	/** Getter for property url.
	 * @return Value of property url.
	 */
	public URL getUrl() {
		return url;
	}

	/** Setter for property url.
	 * @param url New value of property url.
	 */
	public void setUrl(URL url) {
		this.url = url;
	}
}
